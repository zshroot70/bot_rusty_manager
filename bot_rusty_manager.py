import subprocess
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

TOKEN = 'SEU_TOKEN'  # Substitua pelo seu token
ALLOWED_USER_ID = 123456789  # Substitua pelo seu ID de usuário

def start(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ALLOWED_USER_ID:
        update.message.reply_text("Você não tem permissão para usar este bot.")
        return
    
    update.message.reply_text('Olá! Escolha uma ação:', reply_markup=main_menu())

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("Usuários", callback_data='usuarios'),
            InlineKeyboardButton("Relatórios", callback_data='relatorios')
        ],
        [
            InlineKeyboardButton("Configurações", callback_data='configuracoes')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def usuarios_keyboard():
    keyboard = [
        [InlineKeyboardButton("Criar Usuário", callback_data='criar_usuario')],
        [InlineKeyboardButton("Remover Usuário", callback_data='remover_usuario')],
        [InlineKeyboardButton("Gerar Teste", callback_data='gerar_teste')],
        [InlineKeyboardButton("Voltar ao Menu Principal", callback_data='voltar_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def relatorios_keyboard():
    keyboard = [
        [InlineKeyboardButton("Relatório de Usuários", callback_data='relatorio_usuarios')],
        [InlineKeyboardButton("Relatório de Expirados", callback_data='relatorio_expirados')],
        [InlineKeyboardButton("Relatório Online", callback_data='relatorio_online')],
        [InlineKeyboardButton("Voltar ao Menu Principal", callback_data='voltar_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def configuracoes_keyboard():
    keyboard = [
        [InlineKeyboardButton("Alterar Limite", callback_data='alterar_limite')],
        [InlineKeyboardButton("Alterar Validade", callback_data='alterar_validade')],
        [InlineKeyboardButton("Alterar Senha", callback_data='alterar_senha')],
        [InlineKeyboardButton("Voltar ao Menu Principal", callback_data='voltar_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def button(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ALLOWED_USER_ID:
        update.callback_query.answer("Você não tem permissão para usar este bot.")
        return
    
    query = update.callback_query
    query.answer()

    if query.data == 'usuarios':
        query.edit_message_text(text="Escolha uma ação para Usuários:", reply_markup=usuarios_keyboard())
    
    elif query.data == 'relatorios':
        query.edit_message_text(text="Escolha um relatório:", reply_markup=relatorios_keyboard())
    
    elif query.data == 'configuracoes':
        query.edit_message_text(text="Escolha uma configuração:", reply_markup=configuracoes_keyboard())

    elif query.data == 'voltar_menu':
        query.edit_message_text(text='Olá! Escolha uma ação:', reply_markup=main_menu())

    elif query.data == 'criar_usuario':
        query.edit_message_text(text="Envie o nome do usuário:")
        context.user_data['action'] = 'esperando_usuario'

    elif query.data == 'remover_usuario':
        query.edit_message_text(text="Envie o nome do usuário que deseja remover:")
        context.user_data['action'] = 'esperando_usuario_remover'

    elif query.data == 'gerar_teste':
        query.edit_message_text(text="Envie a duração do teste em minutos:")
        context.user_data['action'] = 'esperando_teste_duracao'

    elif query.data == 'alterar_validade':
        query.edit_message_text(text="Envie o nome do usuário cuja validade você deseja alterar:")
        context.user_data['action'] = 'esperando_usuario_validade'

    elif query.data == 'alterar_limite':
        query.edit_message_text(text="Envie o nome do usuário cujo limite você deseja alterar:")
        context.user_data['action'] = 'esperando_usuario_limite'

    elif query.data == 'alterar_senha':
        query.edit_message_text(text="Envie o nome do usuário cuja senha você deseja alterar:")
        context.user_data['action'] = 'esperando_usuario_senha'

    # Relatórios
    elif query.data == 'relatorio_usuarios':
        resposta = executar_comando(['/opt/rustymanager/manager', '--users-report'])
        query.edit_message_text(text=format_report(resposta))
        query.edit_message_reply_markup(reply_markup=main_menu())

    elif query.data == 'relatorio_expirados':
        resposta = executar_comando(['/opt/rustymanager/manager', '--expired-report'])
        query.edit_message_text(text=format_report(resposta))
        query.edit_message_reply_markup(reply_markup=main_menu())

    elif query.data == 'relatorio_online':
        resposta = executar_comando(['/opt/rustymanager/manager', '--online-report'])
        query.edit_message_text(text=format_report(resposta))
        query.edit_message_reply_markup(reply_markup=main_menu())

def handle_message(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ALLOWED_USER_ID:
        update.message.reply_text("Você não tem permissão para usar este bot.")
        return

    action = context.user_data.get('action')

    if action == 'esperando_usuario':
        context.user_data['usuario'] = update.message.text
        update.message.reply_text("Usuário recebido! Agora, envie a senha:")
        context.user_data['action'] = 'esperando_senha'

    elif action == 'esperando_senha':
        context.user_data['senha'] = update.message.text
        update.message.reply_text("Senha recebida! Agora, envie a validade (em dias):")
        context.user_data['action'] = 'esperando_validade'

    elif action == 'esperando_validade':
        validade = update.message.text
        if not validade.isdigit():
            update.message.reply_text("Por favor, insira um número válido para a validade (em dias).")
            return
        context.user_data['validade'] = validade
        update.message.reply_text("Validade recebida! Agora, envie o limite de conexões:")
        context.user_data['action'] = 'esperando_limite'

    elif action == 'esperando_limite':
        limite = update.message.text
        if not limite.isdigit():
            update.message.reply_text("Por favor, insira um número válido para o limite de conexões.")
            return
        usuario = context.user_data.get('usuario')
        senha = context.user_data.get('senha')
        validade = context.user_data.get('validade')

        comando = ['/opt/rustymanager/manager', '--create-user', usuario, senha, validade, limite]
        resposta = executar_comando(comando)
        update.message.reply_text(resposta)

        # Voltar ao menu principal
        update.message.reply_text('Escolha uma ação:', reply_markup=main_menu())
        context.user_data.clear()

    elif action == 'esperando_usuario_validade':
        usuario = update.message.text
        context.user_data['usuario_validade'] = usuario
        update.message.reply_text("Usuário recebido! Agora, envie a nova validade (em dias):")
        context.user_data['action'] = 'esperando_nova_validade'

    elif action == 'esperando_nova_validade':
        nova_validade = update.message.text
        if not nova_validade.isdigit():
            update.message.reply_text("Por favor, insira um número válido para a nova validade (em dias).")
            return

        usuario = context.user_data.get('usuario_validade')
        comando = ['/opt/rustymanager/manager', '--change-validity', usuario, nova_validade]
        resposta = executar_comando(comando)
        update.message.reply_text(resposta)

        # Voltar ao menu principal
        update.message.reply_text('Escolha uma ação:', reply_markup=main_menu())
        context.user_data.clear()

    elif action == 'esperando_usuario_limite':
        usuario = update.message.text
        context.user_data['usuario_limite'] = usuario
        update.message.reply_text("Usuário recebido! Agora, envie o novo limite de conexões:")
        context.user_data['action'] = 'esperando_novo_limite'

    elif action == 'esperando_novo_limite':
        novo_limite = update.message.text
        if not novo_limite.isdigit():
            update.message.reply_text("Por favor, insira um número válido para o novo limite de conexões.")
            return

        usuario = context.user_data.get('usuario_limite')
        comando = ['/opt/rustymanager/manager', '--change-limit', usuario, novo_limite]
        resposta = executar_comando(comando)
        update.message.reply_text(resposta)

        # Voltar ao menu principal
        update.message.reply_text('Escolha uma ação:', reply_markup=main_menu())
        context.user_data.clear()

    elif action == 'esperando_usuario_senha':
        usuario = update.message.text
        context.user_data['usuario_senha'] = usuario
        update.message.reply_text("Usuário recebido! Agora, envie a nova senha:")
        context.user_data['action'] = 'esperando_nova_senha'

    elif action == 'esperando_nova_senha':
        nova_senha = update.message.text
        usuario = context.user_data.get('usuario_senha')
        comando = ['/opt/rustymanager/manager', '--change-pass', usuario, nova_senha]
        resposta = executar_comando(comando)
        update.message.reply_text(resposta)

        # Voltar ao menu principal
        update.message.reply_text('Escolha uma ação:', reply_markup=main_menu())
        context.user_data.clear()

    elif action == 'esperando_usuario_remover':
        usuario = update.message.text
        comando = ['/opt/rustymanager/manager', '--remove-user', usuario]
        resposta = executar_comando(comando)
        update.message.reply_text(resposta)

        # Voltar ao menu principal
        update.message.reply_text('Escolha uma ação:', reply_markup=main_menu())
        context.user_data.clear()

    elif action == 'esperando_teste_duracao':
        duracao = update.message.text
        if not duracao.isdigit():
            update.message.reply_text("Por favor, insira um número válido para a duração do teste em minutos.")
            return

        comando = ['/opt/rustymanager/manager', '--generate-test', duracao]
        resposta = executar_comando(comando)
        update.message.reply_text(resposta)

        # Voltar ao menu principal
        update.message.reply_text('Escolha uma ação:', reply_markup=main_menu())
        context.user_data.clear()

def format_report(data: str) -> str:
    try:
        json_data = json.loads(data)
        formatted_lines = []
        for entry in json_data:
            user = entry.get('user', 'Desconhecido')
            connected = entry.get('connected', '0')
            limit = entry.get('limit', 'N/A')
            line = f"Usuário: {user}, Conectado: {connected}, Limite: {limit}"
            formatted_lines.append(line)
        return "\n".join(formatted_lines) if formatted_lines else "Nenhum dado encontrado."
    except json.JSONDecodeError:
        return "Erro ao processar os dados. Saída não é um JSON válido."

def executar_comando(comando: list) -> str:
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True)
        return resultado.stdout if resultado.stdout else 'Nenhuma saída do comando.'
    except Exception as e:
        return f'Ocorreu um erro: {e}'

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
