from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_approve_kb(user_id: int) -> InlineKeyboardMarkup:
    """Keyboard for admin to approve or reject a driver application."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить",
                    callback_data=f"approve_driver:{user_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject_driver:{user_id}",
                )
            ]
        ]
    )


def admin_panel_kb(is_main_admin: bool = False) -> InlineKeyboardMarkup:
    """Main admin panel keyboard."""
    buttons = [
        [
            InlineKeyboardButton(
                text="👥 Управление водителями",
                callback_data="admin_drlist",
            )
        ],
        [
            InlineKeyboardButton(
                text="➕ Добавить водителя",
                callback_data="admin_add_drv",
            )
        ]
    ]
    if is_main_admin:
        buttons.append([
            InlineKeyboardButton(
                text="🔑 Изменить код доступа",
                callback_data="admin_change_code",
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text="🛡️ Доп. администраторы",
                callback_data="admin_admins_list",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_admins_list_kb(admins: list[dict]) -> InlineKeyboardMarkup:
    """List of secondary admins."""
    keyboard = []
    for adm in admins:
        keyboard.append([
            InlineKeyboardButton(text=f"Админ: {adm['name']}", callback_data=f"admin_view_admin:{adm['id']}")
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад в меню", callback_data="admin_panel_back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def admin_admin_manage_kb(user_id: int) -> InlineKeyboardMarkup:
    """Manage a specific secondary admin."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Забрать права", callback_data=f"admin_revoke_admin:{user_id}")],
            [InlineKeyboardButton(text="🔙 К списку админов", callback_data="admin_admins_list")]
        ]
    )

def admin_drivers_list_kb(drivers: list) -> InlineKeyboardMarkup:
    """Keyboard with a list of active drivers."""
    keyboard = []
    for d in drivers:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"🚗 {d.name} ({d.car_model})",
                    callback_data=f"admin_drv:{d.user_id}",
                )
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                text="🔙 Назад в меню",
                callback_data="admin_panel_back",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def admin_driver_manage_kb(user_id: int) -> InlineKeyboardMarkup:
    """Manage a specific driver."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Блокировать (удалить)",
                    callback_data=f"admin_del_drv:{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 К списку",
                    callback_data="admin_drlist",
                )
            ]
        ]
    )
