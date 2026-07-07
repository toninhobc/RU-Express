from datetime import datetime
import sys
from colorama import init, Fore, Style

init()  # Initialize colorama for cross-platform colored output

# Use relative imports when running as module, or absolute when running from project root
try:
    from catraca_client.db import make_connection
    from catraca_client.queries import QueryUserInfo, QueryCatracaInfo, QueryFastPassValido
except ImportError:
    from db import make_connection
    from queries import QueryUserInfo, QueryCatracaInfo, QueryFastPassValido


class CatracaClient:
    """Client for interacting with a turnstile (catraca) in the RU system.

    Args:
        fastpass_only: If True, the catraca will only allow access to users
                       who have a valid FastPass for the current restaurant and time.
                       If False, normal debit rules apply (FastPass is optional).
    """

    def __init__(self, fastpass_only: bool = False):
        self.fastpass_only = fastpass_only

    def get_user_info(self, cursor, usuario_id: int):
        cursor.execute(QueryUserInfo, (usuario_id,))
        return cursor.fetchone()

    def get_catraca_info(self, cursor, catraca_id: int):
        cursor.execute(QueryCatracaInfo, (catraca_id,))
        return cursor.fetchone()

    def get_fastpass_valido(self, cursor, usuario_id: int, refeitorio_id: int, agora: datetime):
        cursor.execute(QueryFastPassValido, (usuario_id, refeitorio_id, agora))
        return cursor.fetchone()

    def register_access(self, conn, usuario_id: int, catraca_id: int, refeitorio_id: int):
        """Register access in Acesso_RU table"""
        cursor = conn.cursor(dictionary=True)
        agora = datetime.now()

        try:
            # Get user info for validation
            user = self.get_user_info(cursor, usuario_id)
            if not user:
                cursor.close()
                return None, "Usuário não encontrado"

            saldo_anterior = user["saldo_atual"]

            # Check for FastPass (now with horario validation)
            fastpass = self.get_fastpass_valido(cursor, usuario_id, refeitorio_id, agora)

            # If fastpass_only mode, require a valid FastPass
            if self.fastpass_only:
                if not fastpass:
                    cursor.close()
                    return None, "Acesso negado: catraca FastPass exige bilhete FastPass válido para este horário e refeitório"

            # Insert access - trigger will handle valor_cobrado and saldo deduction
            cursor.execute(
                "INSERT INTO Acesso_RU (id_usuario, id_catraca, data_hora_entrada, valor_cobrado) VALUES (%s, %s, %s, NULL)",
                (usuario_id, catraca_id, agora),
            )
            conn.commit()

            # If FastPass was used, mark it as Utilizado
            if fastpass:
                cursor.execute(
                    "UPDATE Bilhete_FastPass SET status_uso = 'Utilizado' WHERE id_bilhete = %s",
                    (fastpass["id_bilhete"],),
                )
                conn.commit()

            # Get updated balance
            cursor.execute(
                "SELECT saldo_atual FROM Usuario_RU WHERE id_usuario = %s",
                (usuario_id,),
            )
            row = cursor.fetchone()
            novo_saldo = row["saldo_atual"] if row else saldo_anterior

            # Get access info (including tipo_refeicao set by trigger)
            cursor.execute(
                "SELECT id_acesso, tipo_refeicao, valor_cobrado FROM Acesso_RU WHERE id_usuario = %s ORDER BY id_acesso DESC LIMIT 1",
                (usuario_id,),
            )
            acesso = cursor.fetchone()

        except Exception as e:
            conn.rollback()
            cursor.close()
            error_msg = str(e)
            # Check if it's a balance constraint error
            if "saldo_atual" in error_msg or "CHECK constraint" in error_msg or "128" in error_msg:
                return None, "Saldo insuficiente"
            return None, f"Erro: {error_msg}"

        cursor.close()

        return {
            "usuario": user["nome"],
            "categoria": user["nome_categoria"],
            "saldo_anterior": float(saldo_anterior),
            "saldo_atual": float(novo_saldo),
            "valor_cobrado": float(acesso["valor_cobrado"]) if acesso["valor_cobrado"] else 0,
            "tipo_refeicao": acesso["tipo_refeicao"],
            "fastpass_usado": fastpass is not None,
        }, None


def main():
    print(f"{Style.BRIGHT}=== Catraca RU-Express ===")
    print(f"{Style.RESET_ALL}")

    # Connect to database
    try:
        conn = make_connection()
    except Exception as e:
        print(f"{Fore.RED}❌ Erro de conexão com o banco: {e}{Style.RESET_ALL}")
        sys.exit(1)

    # Prompt for catraca ID
    try:
        catraca_id = int(input("ID da Catraca: "))
    except ValueError:
        print(f"{Fore.RED}❌ ID inválido{Style.RESET_ALL}")
        conn.close()
        sys.exit(1)

    cursor = conn.cursor(dictionary=True)
    catraca_info = None
    try:
        client = CatracaClient()
        catraca_info = client.get_catraca_info(cursor, catraca_id)
    finally:
        cursor.close()

    if not catraca_info:
        print(f"{Fore.RED}❌ Catraca não encontrada{Style.RESET_ALL}")
        conn.close()
        sys.exit(1)

    print(f"{Fore.GREEN}✓ Catraca conectada: {catraca_info['nome_refeitorio']} - {catraca_info['nome_ru']}{Style.RESET_ALL}")

    refeitorio_id = catraca_info["id_refeitorio"]

    # Ask if this is a FastPass catraca
    fastpass_input = input(f"{Style.BRIGHT}[INPUT] Esta catraca é FastPass? (s/N): {Style.RESET_ALL}").strip().lower()
    fastpass_only = fastpass_input == "s"
    client = CatracaClient(fastpass_only=fastpass_only)

    if fastpass_only:
        print(f"{Fore.YELLOW}⚡ Modo FastPass ativado: apenas usuários com FastPass válido poderão acessar{Style.RESET_ALL}")
    print()

    while True:
        try:
            user_input = input(f"{Style.BRIGHT}[INPUT] Digite ID do usuário (q para sair): {Style.RESET_ALL}").strip()
        except EOFError:
            break

        if user_input.lower() == "q":
            print("Saindo...")
            break

        try:
            usuario_id = int(user_input)
        except ValueError:
            print(f"{Fore.RED}❌ ID inválido{Style.RESET_ALL}")
            continue

        result, error = client.register_access(conn, usuario_id, catraca_id, refeitorio_id)

        if error:
            print(f"  {Fore.RED}❌ {error}{Style.RESET_ALL}")
            continue

        # Success output
        print(f"  {Fore.GREEN}✅ ACESSO AUTORIZADO{Style.RESET_ALL}")
        print(f"  {Style.BRIGHT}Usuário:{Style.RESET_ALL} {result['usuario']} ({result['categoria']})")
        print(f"  {Style.BRIGHT}Saldo anterior:{Style.RESET_ALL} R$ {result['saldo_anterior']:.2f}")

        if result["fastpass_usado"]:
            print(f"  {Fore.GREEN}FastPass utilizado!{Style.RESET_ALL}")
            print(f"  {Style.BRIGHT}Valor cobrado:{Style.RESET_ALL} R$ 0.00")
        else:
            print(f"  {Style.BRIGHT}Valor cobrado:{Style.RESET_ALL} R$ {result['valor_cobrado']:.2f}")

        print(f"  {Style.BRIGHT}Saldo atual:{Style.RESET_ALL} R$ {result['saldo_atual']:.2f}")
        print(f"  {Style.BRIGHT}Refeição:{Style.RESET_ALL} {result['tipo_refeicao']}")
        print()

    conn.close()


if __name__ == "__main__":
    main()