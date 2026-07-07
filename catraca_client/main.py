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


def get_user_info(cursor, usuario_id: int):
    cursor.execute(QueryUserInfo, (usuario_id,))
    return cursor.fetchone()


def get_catraca_info(cursor, catraca_id: int):
    cursor.execute(QueryCatracaInfo, (catraca_id,))
    return cursor.fetchone()


def get_fastpass_valido(cursor, usuario_id: int, refeitorio_id: int):
    cursor.execute(QueryFastPassValido, (usuario_id, refeitorio_id))
    return cursor.fetchone()


def register_access(conn, usuario_id: int, catraca_id: int, refeitorio_id: int):
    """Register access in Acesso_RU table"""
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get user info for validation
        user = get_user_info(cursor, usuario_id)
        if not user:
            cursor.close()
            return None, "Usuário não encontrado"
        
        saldo_anterior = user["saldo_atual"]
        
        # Check for FastPass
        fastpass = get_fastpass_valido(cursor, usuario_id, refeitorio_id)
        
        # Insert access - trigger will handle valor_cobrado and saldo deduction
        cursor.execute(
            "INSERT INTO Acesso_RU (id_usuario, id_catraca, data_hora_entrada, valor_cobrado) VALUES (%s, %s, %s, NULL)",
            (usuario_id, catraca_id, datetime.now()),
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
    catraca = get_catraca_info(cursor, catraca_id)
    if not catraca:
        print(f"{Fore.RED}❌ Catraca não encontrada{Style.RESET_ALL}")
        conn.close()
        sys.exit(1)
    
    print(f"{Fore.GREEN}✓ Catraca conectada: {catraca['nome_refeitorio']} - {catraca['nome_ru']}{Style.RESET_ALL}")
    cursor.close()
    
    refeitorio_id = catraca["id_refeitorio"]
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
        
        result, error = register_access(conn, usuario_id, catraca_id, refeitorio_id)
        
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