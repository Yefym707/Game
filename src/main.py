# Вставлены/обновлены фрагменты, которые вызывают перемещение врагов и взаимодействие с торговцем.
# Предполагается, что остальной main.py остался, здесь — ключевые правки.

# ... внутри игрового цикла, после действий игрока ...

# Перемещение врагов: теперь передаём campaign, чтобы движение могло учитывать ночь
campaign.enemies.move_towards_player(
    campaign.game_map.player_pos,
    campaign.game_map.width,
    campaign.game_map.height,
    campaign
)

# Атака врагов по игроку (оставляем совместимость — Enemy.perform_attack возвращает эффект или None)
enemy = campaign.enemies.get_enemy_at(campaign.game_map.player_pos)
if enemy:
    result = enemy.perform_attack(campaign)
    print("Враг атакует вас!")
    if result:
        print(f"Вы получили эффект: {result}")

# Функция взаимодействия с торговцем — уже использует campaign при вызове методов торговца.
def interact_with_trader(campaign):
    trader = campaign.get_trader_at_player()
    if not campaign.game_map.get_zone_at(campaign.game_map.player_pos) or campaign.game_map.get_zone_at(campaign.game_map.player_pos).zone_type != "merchant":
        print("Здесь нет торговца.")
        return
    if not trader:
        print("Торговец сейчас недоступен (ночь). Попробуйте позже.")
        return
    print(trader.list_goods(campaign))
    while True:
        action = input("Команда (buy item qty / sell item qty / exit): ").strip().lower()
        if action == "exit":
            break
        parts = action.split()
        if len(parts) < 3:
            print("Неверная команда. Пример: buy еда 2")
            continue
        cmd, item, qty = parts[0], parts[1], int(parts[2])
        if cmd == "buy":
            print(trader.sell_to_player(item, campaign.inventory, qty, campaign))
        elif cmd == "sell":
            print(trader.buy_from_player(item, campaign.inventory, qty, campaign))
        else:
            print("Неизвестная команда.")