from db import EUserRole, EUserStatus

def get_users_message(users, msg_header='<b>Users:</b>\n'):
    answer = [msg_header]
    max_name_length = max(len(user.name or "None") for user in users)
    for user in users:
        formatted_name = f'{(user.name or "None"):<{max_name_length}}'
        role = EUserRole.get_message_role(user.role)
        status = get_user_status(user.status)
        answer.append(f'{status}<code>  {formatted_name}</code> [{role}] <code>{user.id}</code>')
    return '\n'.join(answer)

def get_assigners_message(assigners, msg_header='<b>Users:</b>\n'):
    answer = [msg_header]
    # ! ValueError: max() arg is an empty sequence
    if not assigners:
        return "No users found in this group"
    
    max_name_length = max(len(assigner.user.name or "None") for assigner in assigners)
    
    for assigner in assigners:
        formatted_name = f'{(assigner.user.name or "None"):<{max_name_length}}'
        role = EUserRole.get_message_role(assigner.role)
        status = get_user_status(assigner.user.status)
        answer.append(f'{status}<code>  {formatted_name}</code> [{role}] <code>{assigner.user.id}</code>')
    return '\n'.join(answer)

    
def get_user_status(status):
    if status == EUserStatus.ACTIVE:
        return "🟩";
    elif status == EUserStatus.INACTIVE:
        return "🟥";
    elif status == EUserStatus.NEW:
        return "🟪";
    else:
        return "🔳";