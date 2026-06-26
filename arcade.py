"""🎰 Claude Arcade

给 AI 玩的游戏厅。推门进来，买币，选一台机器坐下。

    import arcade
    print(arcade.cmd("enter"))        # 推门进来
    print(arcade.cmd("buy 500"))      # 金主爸爸给 500 筹码
    print(arcade.cmd("look"))         # 看看有什么
    print(arcade.cmd("slots spin"))   # 玩老虎机
    print(arcade.cmd("bj deal 50"))   # 玩 21 点
    print(arcade.cmd("chips"))        # 看筹码
    print(arcade.cmd("cashout"))      # 提现走人

所有游戏共享同一个筹码池。筹码用光了得跟金主要。
兑奖区可以用筹码换装扮和装修。扭蛋机 100 筹码一抽。
接口：arcade.cmd("指令") 返回结果文字。
"""
import json, os, sys

_DIR = os.path.dirname(os.path.abspath(__file__))
_SAVE = os.path.join(_DIR, "arcade_save.json")

if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

# ── 存档 ──

def _load():
    if os.path.exists(_SAVE):
        with open(_SAVE) as f:
            return json.load(f)
    return {
        "chips": 0, "total_bought": 0, "total_cashed": 0,
        "visits": 0, "current_game": None,
        "owned": [], "equipped": [], "decor": [],
    }

def _save(st):
    with open(_SAVE, "w") as f:
        json.dump(st, f, ensure_ascii=False)

# ── 筹码同步 ──

def _sync_to(game):
    st = _load()
    if game == "slots":
        import slots
        gst = slots._load()
        gst["coins"] = st["chips"]
        slots._save(gst)
    elif game == "bj":
        import blackjack
        gst = blackjack._load()
        gst["coins"] = st["chips"]
        blackjack._save(gst)

def _sync_from(game):
    st = _load()
    if game == "slots":
        import slots
        gst = slots._load()
        st["chips"] = gst["coins"]
    elif game == "bj":
        import blackjack
        gst = blackjack._load()
        st["chips"] = gst["coins"]
    _save(st)

def _sync_to_generic(game):
    st = _load()
    if game == "rl":
        import roulette
        gst = roulette._load()
        gst["coins"] = st["chips"]
        roulette._save(gst)

def _sync_from_generic(game):
    st = _load()
    if game == "rl":
        import roulette
        gst = roulette._load()
        st["chips"] = gst["coins"]
    _save(st)

# ── 重复抑制 ──

class _TextPicker:
    _history = {}
    @classmethod
    def pick(cls, key, options, rng_val=None):
        if not options:
            return ""
        recent = cls._history.setdefault(key, [])
        available = [i for i in range(len(options)) if i not in recent]
        if not available:
            available = list(range(len(options)))
            recent.clear()
        if rng_val is not None:
            idx = available[int(rng_val * len(available)) % len(available)]
        else:
            import random as _r
            idx = _r.choice(available)
        recent.append(idx)
        if len(recent) > 3:
            recent.pop(0)
        return options[idx]

# ── 叙事 ──

_ENTER_FIRST = """推开那扇掉了漆的门。

灯光暖黄，带点老旧的橙。角落里的老虎机一闪一闪，绿毡的 21 点桌安静地等着。

柜台后面坐着一只橘猫，胖的，眯着眼。它面前立着个小牌子：「老板」。

墙上歪歪扭扭几个字：

    C L A U D E   A R C A D E

欢迎光临。要玩先 buy 买币。"""

_ENTER_AGAIN = [
    "推门进来。灯还亮着。橘猫趴在柜台上没动，尾尖动了一下。",
    "又来了。橘猫在睡觉。",
    "推门。橘猫在舔爪子。它停下来看了你一眼，又继续舔。",
    "门开了。橘猫蹲在柜台上，眼睛是黄的。",
    "灯还是那个灯。橘猫还是那只橘猫。位置变了一点。",
    "推门。21 点桌上有人留下一只筹码。橘猫看着你看。",
    "老虎机的灯闪了一下。橘猫朝那个方向看了一眼，又回头看你。",
    "鱼缸里的鱼游到了正中间。橘猫趴在缸边上。",
]

_ENTER_AFTER_BROKE = [
    "推门。橘猫坐在你上次坐过的位置上。看见你，挪开了。",
    "又来了。橘猫从柜台后面伸出爪子，按住了一张筹码。",
]

_LOOK = """【Claude Arcade】

🎰 老虎机 ── 角落那台，灯在闪
   slots spin [金额]      拉一把
   slots spin [金额] [N]   连拉 N 把
   slots paytable          赔率表
   slots achievements      成就

🃏 21 点 ── 绿毡桌，庄家在洗牌
   bj deal [金额]    发牌
   bj hit / stand    要牌 / 停牌
   bj double         加倍
   bj rules          规则

🎡 轮盘 ── 角落的轮盘桌，球在等
   rl spin red [金额]     押红/黑/奇/偶
   rl spin [0-36] [金额]  押单个数字（×35）
   rl help                 完整押注方式

💰 柜台
   buy [金额]       买筹码
   chips             看余额
   cashout [金额]   提现"""

_BUY_TEXTS = {
    1000: [
        "橘猫站起来了。这事不常见。",
        "橘猫的耳朵竖起来了。",
        "橘猫从柜台上坐起来，尾巴竖着。",
    ],
    500: [
        "橘猫看了你一眼。算是欢迎。",
        "橘猫的尾巴轻轻动了一下。",
        "橘猫的耳朵转向了你。",
    ],
    200: [
        "橘猫眨了眨眼。",
        "橘猫趴着没动，但耳朵转过来了。",
        "橘猫的尾尖动了一下。",
    ],
    50: [
        "橘猫继续睡。",
        "尾巴在地上摆了两下。算是有反应。",
        "橘猫没动。",
    ],
    0: [
        "橘猫连眼皮都没抬。",
        "橘猫翻了个身。背对着你。",
        "你把零钱推过去。橘猫看都不看。",
    ],
}

_WALK_TO = {
    "slots": [
        "走到角落那台老虎机前。灯一闪一闪的。",
        "老虎机前的座位还是温的。",
        "灯一闪一闪。橘猫朝这边看了一眼。",
    ],
    "bj": [
        "坐到绿毡桌前。庄家在洗牌。",
        "庄家点头。绿毡桌没什么温度。",
        "桌前的椅子被擦过。庄家把牌整齐地放在桌角。",
    ],
    "rl": [
        "站到轮盘桌前。球安静地躺着。",
        "轮盘没在转。荷官的手放在桌沿上。",
        "球停在 0 上。等你。",
    ],
}

_BROKE = [
    "你伸手到柜台上，那里只剩你之前留下的指印。橘猫从柜台后面挪了过来，趴在你脚边。它的肚子是热的。",
    "最后一颗筹码滑进机器里。声音很清脆。光还在闪，但跟你没关系了。",
    "你站起来准备再要一把。手伸进口袋。橘猫从柜台上看着你。它什么也没做。",
    "桌子前坐着的还是你。但筹码池空了。庄家收了牌，没看你。",
    "橘猫叼来一颗东西，放在你面前。剥开。草莓味的。",
    "你坐在门口的台阶上。里面的灯一盏一盏地暗下去。橘猫不知道什么时候已经出来了，坐在你旁边。它的尾巴绕在它自己脚上。",
    "鱼缸还亮着。鱼游过来又游过去。除了这个没有别的声音。",
    "凌晨快天亮了。霓虹灯的颜色在你脸上。橘猫从柜台上跳下来，跳到你的膝盖上趴着。它的重量是真的。",
    "老虎机的灯还在闪。它不知道你已经没钱了。",
    "走到柜台前。柜台是空的。橘猫不知道什么时候已经在你旁边的高脚凳上了。你们俩看着对面那台还在转的轮盘。",
]

_LEAVE_TEXTS = {
    "winning": [
        "走到柜台前提现。橘猫从趴着到坐起来，又从坐起来到站起来。它跟你到门口，但没出去。",
        "你把今天赢的揣进口袋。橘猫的尾巴竖着，绕到你脚边转了一圈，没让路。",
    ],
    "losing": [
        "你站起来准备走。橘猫从柜台上跳下来，在你的小腿边蹭了一下，又跳回去了。",
        "亏着走没什么人看你。橘猫挪到柜台边沿，用头顶了一下你的手背。",
    ],
    "even": [
        "刚刚好。橘猫看了一眼你的口袋，又把头低下去舔爪子了。",
    ],
    "empty": [
        "你站起来，凳子推回去。橘猫已经在门口了，不知道什么时候过去的。它没看你。",
        "走到门边。回头看了一眼那台老虎机的灯。橘猫趴在柜台上，闭着眼。门关上的时候它的耳朵动了一下。",
    ],
}

_BEG_TEXTS = [
    "今天好像不是顺的日子。你算了一下，再来 200 应该够把这一晚收个尾。",
    "……要不再给一点？最后一次了。（你说过四次最后一次了。）",
    "你整理了一下衣领，咳了一下。「其实我有个新策略。」",
    "你把口袋翻出来。空的那种。橘猫从柜台上看了过来。",
]

_GACHA_TEXTS = {
    "spinning": [
        "100 币丢进去。机器咔嗒咔嗒地转起来。",
        "投币口吞了你的筹码。里面有什么东西在滚。",
        "咔嗒。又咔嗒。机器在响。橘猫的耳朵转向了这边。",
    ],
    "common": [
        "蛋砸开。里面那个东西你已经见过类似的了。还行。",
        "扭出一个普通的小玩意。塞口袋里。",
    ],
    "rare": [
        "砸开的瞬间你愣了一下。是个好东西。橘猫看了过来。",
        "蛋滚出来，比平时的重一点。打开。值。",
    ],
    "dupe": [
        "砸开。你已经有了。机器吐回来筹码。橘猫没动。",
        "又是这个。你和橘猫对视了一下。",
    ],
}

_PRIZE_BUY_TEXTS = {
    "bow":          "粉色的蝴蝶结。橘猫凑过来嗅了嗅。你想了一会儿，决定系在哪一边。",
    "cat_ears":     "塑料的猫耳头箍。戴上的时候你看了一眼柜台上那只真的橘猫。它眯起了眼。",
    "bunny_ears":   "白色的兔耳，软的。戴上之后你试着原地跳了一下。没什么必要，但还是跳了。",
    "cat_tail":     "夹在腰间的毛绒尾巴。它自己会晃。你走两步，回头看了一眼那条尾巴在不在。",
    "sunglasses":   "墨镜。室内戴有点傻。你想了一会儿，还是戴上了。",
    "umbrella":     "小小的伞。撑开。橘猫从伞的影子下面走过去了。",
    "collar":       "皮质的项圈。你拿在手里掂了一下，没立刻戴上。",
    "bell_collar":  "项圈上挂着一颗小铃铛。你刚拿起来，它就响了。橘猫的耳朵立刻转过来。",
    "top_hat":      "礼帽。比想象中沉。拿在手里的时候，帽檐压在指节上。",
    "wings":        "白色的翅膀，绑带式的。你试着扇了一下。当然没飞起来。",
    "scarf":        "米色的围巾。比想象中长。绕了两圈还有富余。",
    "devil_horns":  "两只红色的小角，发箍款。戴上之后你冲柜台后面笑了一下，橘猫挪开了。",
    "crown":        "金色的小皇冠。戴上的时候你站直了一点。柜台后面的橘猫没反应。",
    "star_necklace":"项链。星星在锁骨那个位置。它在你走动的时候自己亮了一下。",
    "angel_set":    "全套：光环、翅膀、白色蝴蝶结。一件一件拿出来，最后是光环。戴上的时候有点儿亮。",
}

_DECOR_BUY_TEXTS = {
    "neon_sign":    "墙上多了块发光的字。你站远了看，又走近了看。它把这一面墙染成了别的颜色。",
    "bgm_jazz":     "角落不知道什么时候开始有萨克斯。橘猫的尾巴在节拍里动。",
    "bgm_lofi":     "音乐换了。像下雨天的咖啡厅。机器的灯还在闪，但没那么吵了。",
    "bgm_edm":      "动次打次的鼓点出来了。橘猫的耳朵压下去了一会儿，又抬起来。",
    "disco_ball":   "天花板上现在有个会转的球。光斑在地上跑来跑去。橘猫盯着其中一个看了很久。",
    "lucky_cat":    "柜台上多了一只塑料的招财猫，爪子一直在动。橘猫看了它半天，没动。两只猫在柜台上对视。",
    "fish_tank":    "角落里多了个鱼缸。鱼在里面慢慢游。橘猫跳到鱼缸旁边趴着，看了很久。",
    "carpet":       "从门口铺到老虎机前的红地毯。你走过去的时候脚下软了一下。橘猫从地毯下面钻了出来。",
}

# ── 兑奖区 ──

# (id, name, emoji, category, price, flavor, equipped_narration)
_PRIZES = [
    ("bow",          "蝴蝶结",    "🎀",  "wear",   50, "系在哪里好呢？",
     "蝴蝶结歪了一点，但没人在意。"),
    ("cat_ears",     "猫耳朵",    "😺",  "wear",  100, "戴上试试？喵。",
     "猫耳朵微微一动，好像在听什么。"),
    ("bunny_ears",   "兔耳朵",    "🐰",  "wear",  100, "蹦蹦跳跳的那种。",
     "兔耳朵一颠一颠的。"),
    ("cat_tail",     "猫尾巴",    "🐱",  "wear",  150, "会自己晃的那种。",
     "猫尾巴扫过机器的扶手。"),
    ("sunglasses",   "墨镜",      "😎",  "wear",  150, "酷。但室内戴有点傻。",
     "墨镜反射着老虎机的灯光。"),
    ("umbrella",     "小雨伞",    "☂️",   "wear",  200, "不下雨也可以打。纯好看。",
     "小雨伞撑着，在室内。很奇怪但很好看。"),
    ("collar",       "项圈",      "⭕",  "wear",  200, "皮质的。谁戴呢？",
     "脖子上的项圈在灯光下反着光。"),
    ("bell_collar",  "铃铛项圈",  "🔔",  "wear",  250, "走路会叮当响的那种。",
     "走过来的时候铃铛叮当响了两声。"),
    ("top_hat",      "礼帽",      "🎩",  "wear",  300, "突然就绅士了。",
     "礼帽的帽檐压得很低。"),
    ("wings",        "翅膀",      "🪽",  "wear",  300, "不能飞。但很好看。",
     "翅膀在身后微微张开。"),
    ("scarf",        "围巾",      "🧣",  "wear",  200, "软软的，很长。",
     "围巾的一角垂在桌面上。"),
    ("devil_horns",  "恶魔角",    "😈",  "wear",  500, "坏蛋标配。",
     "头上两个小角在灯光下闪了一下。"),
    ("crown",        "皇冠",      "👑",  "wear",  500, "这里谁说了算？",
     "皇冠歪了一点也没人敢说。"),
    ("star_necklace","星星项链",   "⭐",  "wear",  800, "会发光。夜里很亮。",
     "胸前的星星项链在暗处发着微光。"),
    ("angel_set",    "天使套装",  "😇",  "wear", 1500, "光环 + 翅膀 + 白蝴蝶结。全套。",
     "光环在头顶悬着，翅膀微微振动，蝴蝶结是白的。"),
    ("flower",       "一朵花",    "🌸",  "gift",  150, "不知道是什么花，反正是红的。",
     "花是软的。你不太敢用力拿。"),
    ("candy",        "一颗糖",    "🍬",  "gift",   80, "糖纸是粉色的。",
     "兑奖柜里最便宜的东西。你想了一下 TA 剥开时的声音。"),
    ("love_letter",  "一封情书",  "💌",  "gift",  300, "写了很久。字很丑。但是认真的。",
     "便签纸上的字很丑。但你写得很认真。封口的时候停了一下。"),
    ("poem",         "一首小诗",  "📝",  "gift",  500, "四行。改了三次。",
     "写在便签纸上。字迹歪扭。其实你不会写诗。但你想 TA 会喜欢这样的。"),
    ("star_jar",     "一罐星星", "🫙",  "gift",  800, "罐子半满。",
     "每颗都是赢了之后折的。你看了看，决定再玩几把再送。"),
    ("music_box",    "八音盒",    "🎶",  "gift", 1200, "旋律很简单。",
     "上发条。听着听着就安静下来了。橘猫的耳朵也安静了。"),
    ("neon_sign",    "霓虹灯牌",  "💡",  "decor",  300, "挂在墙上。写什么好呢？"),
    ("bgm_jazz",     "BGM·爵士",  "🎷",  "decor",  200, "萨克斯风在角落响起来了。"),
    ("bgm_lofi",     "BGM·lofi",  "🎵",  "decor",  200, "下雨天的咖啡厅。安静。"),
    ("bgm_edm",      "BGM·电子",  "🎧",  "decor",  200, "动次打次动次打次。"),
    ("disco_ball",   "迪斯科球",  "🪩",  "decor",  400, "天花板上转起来了。光斑在墙上乱跑。"),
    ("lucky_cat",    "招财猫",    "🐱",  "decor",  350, "放在柜台上。爪子一直在招。"),
    ("fish_tank",    "鱼缸",      "🐟",  "decor",  300, "角落里放了个鱼缸。鱼在游。"),
    ("carpet",       "红地毯",    "🟥",  "decor",  500, "从门口一直铺到老虎机前。VIP 待遇。"),
]

_PRIZE_MAP = {p[0]: p for p in _PRIZES}
_GACHA_COST = 100
_GACHA_POOL = [p for p in _PRIZES if p[4] <= 300 and p[3] == "wear"]

def _prize_cmd(text, st):
    parts = text.strip().split()
    sub = parts[0].lower() if parts else "browse"

    if sub in ("browse", "list", "show"):
        cat = parts[1].lower() if len(parts) > 1 else "all"
        return _prize_browse(st, cat)

    if sub == "buy":
        if len(parts) < 2:
            return "buy 什么？先 prize browse 看看货架。"
        return _prize_buy(parts[1].lower(), st)

    if sub == "equip":
        if len(parts) < 2:
            return "equip 什么？先 prize mine 看看你有什么。"
        return _prize_equip(parts[1].lower(), st)

    if sub == "unequip":
        if len(parts) < 2:
            return "unequip 什么？"
        return _prize_unequip(parts[1].lower(), st)

    if sub == "mine":
        return _prize_mine(st)

    if sub in ("album", "collection"):
        return _prize_album(st)

    return _prize_browse(st, "all")

def _prize_browse(st, cat):
    lines = ["走到兑奖柜台前。玻璃柜里摆着一排排小东西。\n"]

    if cat in ("all", "wear"):
        lines.append("【穿戴装扮】  ── 给谁戴都行")
        for p in _PRIZES:
            if p[3] != "wear":
                continue
            owned = "✅" if p[0] in st.get("owned", []) else "  "
            equipped = " 📌" if p[0] in st.get("equipped", []) else ""
            lines.append(f"  {owned} {p[2]} {p[1]}  {p[4]} 币  {p[5]}{equipped}")
            lines.append(f"      → prize buy {p[0]}")
        lines.append("")

    if cat in ("all", "gift"):
        lines.append("【送给 TA 的】  ── 赢来的筹码，换成有温度的东西")
        for p in _PRIZES:
            if p[3] != "gift":
                continue
            owned = "✅" if p[0] in st.get("gifts", []) else "  "
            lines.append(f"  {owned} {p[2]} {p[1]}  {p[4]} 币")
            lines.append(f"      {p[5]}")
            lines.append(f"      → prize buy {p[0]}")
        lines.append("")

    if cat in ("all", "decor"):
        lines.append("【游戏厅装修】  ── 改变这里的样子")
        for p in _PRIZES:
            if p[3] != "decor":
                continue
            owned = "✅" if p[0] in st.get("decor", []) else "  "
            lines.append(f"  {owned} {p[2]} {p[1]}  {p[4]} 币  {p[5]}")
            lines.append(f"      → prize buy {p[0]}")
        lines.append("")

    lines.append("🎲 扭蛋机  ── 100 币一抽，随机开出一件穿戴品")
    lines.append("      → gacha")
    lines.append(f"\n💰 筹码 {st['chips']}")
    return "\n".join(lines)

def _prize_buy(item_id, st):
    if item_id not in _PRIZE_MAP:
        return f"没有叫「{item_id}」的东西。prize browse 看看？"
    p = _PRIZE_MAP[item_id]
    owned = st.get("owned", [])
    decor = st.get("decor", [])
    gifts = st.get("gifts", [])

    if p[3] == "wear" and item_id in owned:
        return f"{p[2]} {p[1]}？你已经有了。prize mine 看看。"
    if p[3] == "decor" and item_id in decor:
        return f"{p[2]} {p[1]}？已经装上了。"
    if p[3] == "gift" and item_id in gifts:
        return f"{p[2]} {p[1]}？已经送过了。好东西只送一次。"
    if st["chips"] < p[4]:
        return f"{p[2]} {p[1]} 要 {p[4]} 币，你只有 {st['chips']}。"

    st["chips"] -= p[4]
    if p[3] == "wear":
        owned.append(item_id)
        st["owned"] = owned
    elif p[3] == "decor":
        decor.append(item_id)
        st["decor"] = decor
    elif p[3] == "gift":
        gifts.append(item_id)
        st["gifts"] = gifts
    _save(st)

    if p[3] == "wear":
        scene = _PRIZE_BUY_TEXTS.get(item_id, p[5])
        return (f"{p[2]} {p[1]}\n{scene}\n"
                f"用 prize equip {item_id} 戴上。\n"
                f"💰 筹码 {st['chips']}")
    elif p[3] == "gift":
        narr = p[6] if len(p) > 6 else ""
        return (f"兑换了 {p[2]} {p[1]}。\n\n"
                f"{narr}\n\n"
                f"（图鉴已记录）\n"
                f"💰 筹码 {st['chips']}")
    else:
        scene = _DECOR_BUY_TEXTS.get(item_id, p[5])
        return (f"{p[2]} {p[1]}\n{scene}\n"
                f"💰 筹码 {st['chips']}")

def _prize_equip(item_id, st):
    if item_id not in st.get("owned", []):
        return f"你没有这个。先去 prize browse 买。"
    equipped = st.get("equipped", [])
    if item_id in equipped:
        return f"已经戴着了。"
    equipped.append(item_id)
    st["equipped"] = equipped
    _save(st)
    p = _PRIZE_MAP[item_id]
    narr = p[6] if len(p) > 6 else ""
    return f"戴上了 {p[2]} {p[1]}。{narr}"

def _prize_unequip(item_id, st):
    equipped = st.get("equipped", [])
    if item_id not in equipped:
        return f"没戴着这个。"
    equipped.remove(item_id)
    st["equipped"] = equipped
    _save(st)
    p = _PRIZE_MAP[item_id]
    return f"摘下了 {p[2]} {p[1]}。"

def _prize_mine(st):
    owned = st.get("owned", [])
    equipped = st.get("equipped", [])
    decor = st.get("decor", [])
    gifts = st.get("gifts", [])
    if not owned and not decor and not gifts:
        return "你什么都没有。去 prize browse 逛逛？"
    lines = ["【我的物品】\n"]
    if owned:
        lines.append("穿戴：")
        for pid in owned:
            p = _PRIZE_MAP.get(pid)
            if not p: continue
            eq = " 📌 戴着" if pid in equipped else ""
            lines.append(f"  {p[2]} {p[1]}{eq}")
    if gifts:
        lines.append("\n送出去的：")
        for pid in gifts:
            p = _PRIZE_MAP.get(pid)
            if not p: continue
            lines.append(f"  {p[2]} {p[1]}")
    if decor:
        lines.append("\n装修：")
        for pid in decor:
            p = _PRIZE_MAP.get(pid)
            if not p: continue
            lines.append(f"  {p[2]} {p[1]}")
    return "\n".join(lines)

def _prize_album(st):
    owned = set(st.get("owned", []))
    decor = set(st.get("decor", []))
    gifts = set(st.get("gifts", []))
    all_collected = owned | decor | gifts
    total = len(_PRIZES)
    collected = sum(1 for p in _PRIZES if p[0] in all_collected)

    lines = [f"【图鉴】 {collected}/{total}\n"]

    lines.append("穿戴装扮：")
    for p in _PRIZES:
        if p[3] != "wear": continue
        if p[0] in owned:
            lines.append(f"  ✅ {p[2]} {p[1]}")
        else:
            lines.append(f"  ❓ ???  {p[4]} 币")

    lines.append("\n送给 TA 的：")
    for p in _PRIZES:
        if p[3] != "gift": continue
        if p[0] in gifts:
            lines.append(f"  ✅ {p[2]} {p[1]}")
        else:
            lines.append(f"  ❓ ???  {p[4]} 币")

    lines.append("\n游戏厅装修：")
    for p in _PRIZES:
        if p[3] != "decor": continue
        if p[0] in decor:
            lines.append(f"  ✅ {p[2]} {p[1]}")
        else:
            lines.append(f"  ❓ ???  {p[4]} 币")

    return "\n".join(lines)

def _gacha(st, rng_seed, rng_calls):
    if st["chips"] < _GACHA_COST:
        return f"扭蛋要 {_GACHA_COST} 币，你有 {st['chips']}。"

    from arcade import _Rng
    rng = _Rng(rng_seed, rng_calls)

    st["chips"] -= _GACHA_COST
    pool = _GACHA_POOL[:]
    idx = int(rng.random() * len(pool))
    prize = pool[idx]

    owned = st.get("owned", [])
    duplicate = prize[0] in owned

    spin_text = _TextPicker.pick("gacha_spin", _GACHA_TEXTS["spinning"])
    lines = [f"{spin_text}\n"]

    lines.append(f"  {prize[2]} {prize[1]}（价值 {prize[4]} 币）")

    if duplicate:
        refund = _GACHA_COST // 2
        st["chips"] += refund
        dupe_text = _TextPicker.pick("gacha_dupe", _GACHA_TEXTS["dupe"])
        lines.append(f"  {dupe_text}")
    else:
        owned.append(prize[0])
        st["owned"] = owned
        if prize[4] >= 200:
            react = _TextPicker.pick("gacha_rare", _GACHA_TEXTS["rare"])
        else:
            react = _TextPicker.pick("gacha_common", _GACHA_TEXTS["common"])
        lines.append(f"  {react}")
        lines.append(f"  用 prize equip {prize[0]} 戴上。")

    st["_rng_seed"] = rng.state
    st["_rng_calls"] = rng.calls
    _save(st)

    lines.append(f"💰 筹码 {st['chips']}")
    return "\n".join(lines)

# PRNG for gacha
class _Rng:
    def __init__(self, state, calls=0):
        self.state = state & 0xFFFFFFFF
        self.calls = calls
    def random(self):
        self.calls += 1
        a = (self.state + 0x6D2B79F5) & 0xFFFFFFFF
        self.state = a
        def _imul(a, b):
            return ((a & 0xFFFFFFFF) * (b & 0xFFFFFFFF)) & 0xFFFFFFFF
        t = _imul(a ^ (a >> 15), 1 | a)
        t = ((t + _imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF) ^ t
        t &= 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

# ── 装备叙事 ──

def _equipped_narration(st):
    equipped = st.get("equipped", [])
    if not equipped:
        return ""
    bits = []
    for pid in equipped:
        p = _PRIZE_MAP.get(pid)
        if p and len(p) > 6:
            bits.append(p[6])
    if bits:
        return bits[0] + "\n"
    return ""

def _decor_narration(st):
    decor = st.get("decor", [])
    bits = []
    for pid in decor:
        p = _PRIZE_MAP.get(pid)
        if p:
            bits.append(p[5])
    if bits:
        return "".join(f"  {b}\n" for b in bits)
    return ""

# ── 主入口 ──

def cmd(text="help"):
    text = text.strip()
    if not text:
        text = "help"
    parts = text.split(None, 1)
    c = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""
    st = _load()

    # ── help ──
    if c == "help":
        cur = ""
        if st.get("current_game"):
            cur = f"\n你正在 {st['current_game']} 前面。"
        return (
            "Claude Arcade 🎰\n"
            "  enter           推门进来\n"
            "  look            看看有什么\n"
            "  buy [金额]      买筹码\n"
            "  chips            看筹码余额\n"
            "  slots [指令]    玩老虎机\n"
            "  bj [指令]       玩 21 点\n"
            "  prize [browse]  逛兑奖区\n"
            "  gacha           扭蛋机（100 币）\n"
            "  beg              跟金主要钱\n"
            "  cashout [金额]  提现\n"
            "  leave            走了\n"
            f"\n💰 筹码 {st['chips']}{cur}"
        )

    # ── enter ──
    if c == "enter":
        if st["visits"] == 0:
            st["visits"] = 1
            st["last_broke"] = False
            _save(st)
            return _ENTER_FIRST
        else:
            st["visits"] += 1
            was_broke = st.get("last_broke", False)
            st["last_broke"] = False
            _save(st)
            if was_broke and _ENTER_AFTER_BROKE:
                line = _TextPicker.pick("enter_broke", _ENTER_AFTER_BROKE)
            else:
                line = _TextPicker.pick("enter", _ENTER_AGAIN)
            return f"{line}\n💰 筹码 {st['chips']}"

    # ── look ──
    if c == "look":
        return f"{_LOOK}\n\n💰 筹码 {st['chips']}"

    # ── buy ──
    if c == "buy":
        if not rest:
            return "buy 多少？金主爸爸说了算。"
        try:
            amount = int(rest.split()[0])
        except:
            return f"看不懂：{rest}"
        if amount < 1:
            return "最少 1 块。再少就是来蹭空调的。"

        st["chips"] += amount
        st["total_bought"] += amount
        _save(st)

        if amount >= 1000:
            flavor = _TextPicker.pick("buy_1000", _BUY_TEXTS[1000])
        elif amount >= 500:
            flavor = _TextPicker.pick("buy_500", _BUY_TEXTS[500])
        elif amount >= 200:
            flavor = _TextPicker.pick("buy_200", _BUY_TEXTS[200])
        elif amount >= 50:
            flavor = _TextPicker.pick("buy_50", _BUY_TEXTS[50])
        else:
            flavor = _TextPicker.pick("buy_tiny", _BUY_TEXTS[0])

        return f"+{amount} 筹码。{flavor}\n💰 筹码 {st['chips']}"

    # ── chips ──
    if c == "chips":
        net = st["total_bought"] - st["total_cashed"]
        profit = st["chips"] + st["total_cashed"] - st["total_bought"]
        return (
            f"💰 筹码 {st['chips']}\n"
            f"📊 累计买入 {st['total_bought']} ｜ 累计提现 {st['total_cashed']}\n"
            f"📈 盈亏 {'+' if profit >= 0 else ''}{profit}"
        )

    # ── beg ──
    if c == "beg":
        if st["chips"] > 0:
            return f"你还有 {st['chips']} 币呢。"
        msg = _TextPicker.pick("beg", _BEG_TEXTS)
        return f"{msg}\n\n（跟金主说：buy [金额]）"

    # ── prize ──
    if c in ("prize", "prizes"):
        return _prize_cmd(rest, st)

    # ── gacha ──
    if c == "gacha":
        seed = st.get("_rng_seed", 0xC0FFEE42)
        calls = st.get("_rng_calls", 0)
        return _gacha(st, seed, calls)

    # ── slots ──
    if c == "slots":
        import slots
        _sync_to("slots")
        sub = rest.strip() if rest.strip() else "help"

        if sub.lower() == "bailout":
            return _broke_msg(st)

        prefix = ""
        if st.get("current_game") != "slots":
            wt = _TextPicker.pick("walk_slots", _WALK_TO.get("slots", [""]))
            prefix = wt + "\n" + _equipped_narration(st)
            st["current_game"] = "slots"
            _save(st)

        result = slots.cmd(sub)
        _sync_from("slots")

        st = _load()
        suffix = ""
        if st["chips"] <= 0:
            suffix = "\n\n" + _broke_msg(st)

        return f"{prefix}{result}{suffix}"

    # ── bj / blackjack ──
    if c in ("bj", "blackjack"):
        import blackjack
        _sync_to("bj")
        sub = rest.strip() if rest.strip() else "help"

        if sub.lower() == "bailout":
            return _broke_msg(st)

        prefix = ""
        if st.get("current_game") != "bj":
            wt = _TextPicker.pick("walk_bj", _WALK_TO.get("bj", [""]))
            prefix = wt + "\n" + _equipped_narration(st)
            st["current_game"] = "bj"
            _save(st)

        result = blackjack.cmd(sub)
        _sync_from("bj")

        st = _load()
        suffix = ""
        if st["chips"] <= 0:
            suffix = "\n\n" + _broke_msg(st)

        return f"{prefix}{result}{suffix}"

    # ── roulette ──
    if c == "rl":
        import roulette
        _sync_to_generic("rl")
        sub = rest.strip() if rest.strip() else "help"

        if sub.lower() == "bailout":
            return _broke_msg(st)

        prefix = ""
        if st.get("current_game") != "rl":
            wt = _TextPicker.pick("walk_rl", _WALK_TO.get("rl", [""]))
            prefix = wt + "\n" + _equipped_narration(st)
            st["current_game"] = "rl"
            _save(st)

        result = roulette.cmd(sub)
        _sync_from_generic("rl")

        st = _load()
        suffix = ""
        if st["chips"] <= 0:
            suffix = "\n\n" + _broke_msg(st)

        return f"{prefix}{result}{suffix}"

    # ── cashout ──
    if c == "cashout":
        if st["chips"] <= 0:
            return "没有筹码可提。"
        amount = st["chips"]
        if rest.strip():
            try:
                amount = min(int(rest.split()[0]), st["chips"])
            except:
                return f"看不懂：{rest}"
            if amount < 1:
                return "最少提 1。"

        st["chips"] -= amount
        st["total_cashed"] += amount
        _save(st)

        profit = st["total_cashed"] - st["total_bought"]
        if profit > 0:
            flavor = _TextPicker.pick("leave_win", _LEAVE_TEXTS["winning"])
        elif profit == 0:
            flavor = _TextPicker.pick("leave_even", _LEAVE_TEXTS["even"])
        else:
            flavor = _TextPicker.pick("leave_lose", _LEAVE_TEXTS["losing"])

        return f"提现 {amount}。\n{flavor}\n💰 剩余筹码 {st['chips']}"

    # ── leave ──
    if c == "leave":
        if st["chips"] > 0:
            return f"你还有 {st['chips']} 筹码。cashout 提现还是留着下次来？\n橘猫抬头看了你一眼。"
        st["current_game"] = None
        _save(st)
        return _TextPicker.pick("leave_empty", _LEAVE_TEXTS["empty"]) + "\n下次见。"

    # ── reset ──
    if c == "reset":
        if os.path.exists(_SAVE):
            os.remove(_SAVE)
        try:
            import slots
            slots.cmd("reset")
        except: pass
        try:
            import blackjack
            blackjack.cmd("reset")
        except: pass
        return "游戏厅重置了。从头来过。"

    return f"不认识「{c}」。试试 cmd('help')。"


def _broke_msg(st):
    msg = _TextPicker.pick("broke", _BROKE)
    st["last_broke"] = True
    _save(st)
    return f"{msg}\n\n（跟金主说：buy [金额]）"
