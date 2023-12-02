import pretty_midi
import os
import random

# 一些用到的方块宏定义
FRAME_BLOCK = "yellow_concrete"     # 框架方块1
DEBUG_BLOCK = "red_concrete"        # 框架方块2
CONNECT_NODE = "redstone_wire"      # 主轴连接用
NOTE_BLOCK = "note_block"           # 音符盒
PRE_BLOCK = "redstone_lamp"         # 前置在音符盒前, 传递中继器信号的方块
REPEATER = "repeater"               # 中继器
REDSTONE_WIRE = "redstone_wire"     # 红石线
OBSERVER = "observer"               # 观察者
STICKY_PISTON = "sticky_piston"     # 粘性活塞
TREE_LOG = "oak_log"                # 树干
TREE_LEAVES = "oak_leaves"          # 树叶



overflow_note_cnt = 0           # 统计超出音域的音符数量
over_bar_capacity_note_cnt = 0  # 因为该小节音符过多(>13)而被舍弃的数量

def get_pitch_and_base(pitch):
    if pitch is None:
        return None, None
    mc_pitch = (pitch - 42) % 24
    base = (pitch - 42) // 24
    if base == 0:
        base_block = "oak_planks"
    elif base == 1:
        base_block = "dirt"
    elif base == 2:
        base_block = "gold_block"
    else:
        return [None, None]
    return mc_pitch, base_block



# second -> game_tick(0.05s)
def sec2gt(sec):
    return int(sec * 20 + 0.5)

# 用 gametick 记录起始时间的音符对象
class Note:
    def __init__(self, gametick, pitch):
        self.gametick = gametick
        self.pitch = pitch
    def __repr__(self):
        return f"gametick={self.gametick}, pitch={self.pitch}"
    def is_first_half(self):
        return self.gametick % 2 == 0
    def is_second_half(self):
        return self.gametick % 2 == 1


class Unit:
    def __init__(self, gt=None):
        self.type = None  # 0 or 1 表示奇偶类型模块, 因为相同的结构的树叶会相连造成干扰;
        self.gt_forGapOnly = gt
        self.first_note = None
        self.second_note = None

    def __repr__(self):
        return f"get_gt():{self.get_gt()} First_Note: {self.first_note}\tSecond_Note: {self.second_note}"

    def get_gt(self):   # 这个单元的first_note的gt(即使这个单元并没有first_note)
        if self.first_note:
            return self.first_note.gametick
        elif self.second_note:
            return self.second_note.gametick - 1
        elif self.is_gap():
            return self.gt_forGapOnly
        else:
            raise ValueError("未知错误")

    def is_gap(self):
        return self.first_note is None and self.second_note is None


class Block:
    def __init__(self, x, y, z, block_type, **info):
        self.x, self.y, self.z = x, y, z
        self.block_type = block_type
        self.info = info



X, Y, Z = 11, 21, -163  # 设置"建造原点"坐标, 默认为(0,64,0)
BAR_AMOUNT = 99     # 设置midi的小节数量上限
MIDI_FILE_NAME = "Flight of the Bumblebee (300bpm).mid"  # 待读取的midi文件名(.mid后缀不可省略)
MINECRAFT_SAVE_PATH = "/Users/cuipy/Library/Application Support/minecraft/saves/rsm_demo"   # Minecraft存档路径(最后不要加"/")
FUNCTION_FOLDER = MINECRAFT_SAVE_PATH + "/datapacks/rsm/data/rsm/functions/"        # 通过存档路径计算function路径

# 新建一个只包含自定义function的资源包
try:
    os.makedirs(MINECRAFT_SAVE_PATH + "/datapacks/rsm/data/rsm/functions")
except FileExistsError:
    print("此目录已存在, 不再重复创建")
with open(MINECRAFT_SAVE_PATH + "/datapacks/rsm/pack.mcmeta", 'w') as f:
    print("""{"pack":{"pack_format":4,"description":"redstone_functions"}}""", end='', file=f)



# 读取文件为PrettyMIDI格式
midi_data = pretty_midi.PrettyMIDI(MIDI_FILE_NAME)

# L/R两个声道
channel_L = midi_data.instruments[0]
channel_R = midi_data.instruments[1]

# 统计两个声道的音符为Note()对象
notes_L = []
notes_R = []
for note in channel_L.notes:
    notes_L.append(Note(sec2gt(note.start), note.pitch))
for note in channel_R.notes:
    notes_R.append(Note(sec2gt(note.start), note.pitch))

# 按照起始gt排序
notes_L.sort(key=lambda note: note.gametick)
notes_R.sort(key=lambda note: note.gametick)


bars_L = [[], ]
bars_R = [[], ]

# bars contains bar
# bar contains Unit()
# Unit has (at most) 2 Note()

for note in notes_L:
    if get_pitch_and_base(note.pitch)[0] is None:   # 超出音域的音符!
        print(f"删除了一个超出音域的Note(): {note}")
        overflow_note_cnt += 1
        continue
    if note.gametick / 32 >= len(bars_L):    # 需要新的小节(bar)了
        bars_L.append([])   # 压入一个新的小节(bar)

    if note.is_second_half() and (bars_L[-1]) and (bars_L[-1][-1].second_note is None) and (note.gametick - bars_L[-1][-1].first_note.gametick == 1): # 新的音符可以蹭上一个音符的空位
        bars_L[-1][-1].second_note = note
    else:
        bars_L[-1].append(Unit())   # 蹭不了空位, 需要新建一个单元
        if note.is_first_half():
            bars_L[-1][-1].first_note = note
        else:
            bars_L[-1][-1].second_note = note

for note in notes_R:
    if get_pitch_and_base(note.pitch)[0] is None:   # 超出音域的音符!
        print(f"删除了一个超出音域的Note():{note}")
        overflow_note_cnt += 1
        continue
    if note.gametick / 32 >= len(bars_R):    # 需要新的小节(bar)了
        bars_R.append([])   # 压入一个新的小节(bar)

    if note.is_second_half() and (bars_R[-1]) and (bars_R[-1][-1].second_note is None) and (note.gametick - bars_R[-1][-1].first_note.gametick == 1): # 新的音符可以蹭上一个音符的空位
        bars_R[-1][-1].second_note = note
    else:
        bars_R[-1].append(Unit())   # 蹭不了空位, 需要新建一个单元
        if note.is_first_half():
            bars_R[-1][-1].first_note = note
        else:
            bars_R[-1][-1].second_note = note



# 在 bars_L 的每个小节中额外插入"None Unit", 表示1拍(0.4s, 8gt)的间隔
# 这一过程让 sort() 来实现就好: 给每个小节插入3个不包含音符,但包含gt信息的Unit(), 然后给这个小节排序
for i, bar in enumerate(bars_L):
    bar.append(Unit(gt=i * 32 + 7.5))
    bar.append(Unit(gt=i * 32 + 15.5))
    bar.append(Unit(gt=i * 32 + 23.5))
    bar.sort(key=lambda unit: unit.get_gt())

# 在 bars_R 的每个小节中额外插入"None Unit", 表示1拍(0.4s, 8gt)的间隔
# 这一过程让 sort() 来实现就好: 给每个小节插入3个不包含音符,但包含gt信息的Unit(), 然后给这个小节排序
for i, bar in enumerate(bars_R):
    bar.append(Unit(gt=i * 32 + 7.5))
    bar.append(Unit(gt=i * 32 + 15.5))
    bar.append(Unit(gt=i * 32 + 23.5))
    bar.sort(key=lambda unit: unit.get_gt())



MAX0, MAX1, MAX2, MAX3 = 13, 15, 15, 15

# 检查 L 小节是否有某个节拍具有过多的音(第0拍:max=13, 1~3拍:max=15)
for bar in bars_L:
    # 先找到 3 个 None Unit 的 index
    indices = []
    for idx, unit in enumerate(bar):
        if unit.is_gap():
            indices.append(idx)
    # 统计每个节拍的音符数
    notes_beat0 = indices[0]
    notes_beat1 = indices[1] - indices[0] - 1
    notes_beat2 = indices[2] - indices[1] - 1
    notes_beat3 = len(bar) - indices[2] - 1
    # 如果某个节拍的音符过多(第0拍>13, 1~3拍>15), 随机删除(其实优先删单音会更好..但目前先不优化这里了)一些直到满足.
    # 由于list会"下标移动", 所以先设置删除标记, 最后统一从后向前删除(del)
    if notes_beat3 > MAX3:
        del_amount = notes_beat3 - MAX3
        for i in random.sample(range(indices[2] + 1, len(bar)), del_amount):
            print(f"删除了一个Unit(): {bar[i]}")
            bar[i] = None    # 标记这个unit一会要被删除
    if notes_beat2 > MAX2:
        del_amount = notes_beat2 - MAX2
        for i in random.sample(range(indices[1] + 1, indices[2]), del_amount):
            print(f"删除了一个Unit(): {bar[i]}")
            bar[i] = None    # 标记这个unit一会要被删除
    if notes_beat1 > MAX1:
        del_amount = notes_beat1 - MAX1
        for i in random.sample(range(indices[0] + 1, indices[1]), del_amount):
            print(f"删除了一个Unit(): {bar[i]}")
            bar[i] = None    # 标记这个unit一会要被删除
    if notes_beat0 > MAX0:
        del_amount = notes_beat0 - MAX0
        for i in random.sample(range(indices[0]), del_amount):
            print(f"删除了一个Unit(): {bar[i]}")
            bar[i] = None    # 标记这个unit一会要被删除
    # 删除所有带标记的音符.
    for i in range(len(bar) - 1, -1, -1):
        if bar[i] is None:
            del bar[i]
            over_bar_capacity_note_cnt += 1

# 检查 R 小节是否有某个节拍具有过多的音(第0拍:max=13, 1~3拍:max=15)
for bar in bars_R:
    # 先找到 3 个 None Unit 的 index
    indices = []
    for idx, unit in enumerate(bar):
        if unit.is_gap():
            indices.append(idx)
    # 统计每个节拍的音符数
    notes_beat0 = indices[0]
    notes_beat1 = indices[1] - indices[0] - 1
    notes_beat2 = indices[2] - indices[1] - 1
    notes_beat3 = len(bar) - indices[2] - 1
    # 如果某个节拍的音符过多(第0拍>13, 1~3拍>15), 随机删除(其实优先删单音会更好..但目前先不优化这里了)一些直到满足.
    # 由于list会"下标移动", 所以先设置删除标记, 最后统一从后向前删除(del)
    if notes_beat3 > MAX3:
        del_amount = notes_beat3 - MAX3
        for i in random.sample(range(indices[2] + 1, len(bar)), del_amount):
            print(f"删除了一个Unit(): {bar[i]}")
            bar[i] = None    # 标记这个unit一会要被删除
    if notes_beat2 > MAX2:
        del_amount = notes_beat2 - MAX2
        for i in random.sample(range(indices[1] + 1, indices[2]), del_amount):
            print(f"删除了一个Unit(): {bar[i]}")
            bar[i] = None    # 标记这个unit一会要被删除
    if notes_beat1 > MAX1:
        del_amount = notes_beat1 - MAX1
        for i in random.sample(range(indices[0] + 1, indices[1]), del_amount):
            print(f"删除了一个Unit(): {bar[i]}")
            bar[i] = None    # 标记这个unit一会要被删除
    if notes_beat0 > MAX0:
        del_amount = notes_beat0 - MAX0
        for i in random.sample(range(indices[0]), del_amount):
            print(f"删除了一个Unit(): {bar[i]}")
            bar[i] = None    # 标记这个unit一会要被删除
    # 删除所有带标记的音符.
    for i in range(len(bar) - 1, -1, -1):
        if bar[i] is None:
            del bar[i]
            over_bar_capacity_note_cnt += 1



# 为 bars_L 的每个 Unit() 用设定奇偶值(type = 0 or 1)
for bar in bars_L:
    temp = 0
    for unit in bar:
        temp = not temp
        if unit.is_gap():
            continue
        unit.type = int(temp)


# 为 bars_R 的每个 Unit() 用设定奇偶值(type = 0 or 1)
for bar in bars_R:
    temp = 0
    for unit in bar:
        temp = not temp
        if unit.is_gap():
            continue
        unit.type = int(temp)



# 向world添加一个奇Unit
def build_odd(x, y, z, world, gt, first_note=None, second_note=None):
    first_pitch = first_note.pitch if first_note else None
    second_pitch = second_note.pitch if second_note else None
    # 结构方块
    world.append(Block(x + 0, y, z, FRAME_BLOCK))
    world.append(Block(x + 1, y, z, FRAME_BLOCK))
    world.append(Block(x + 2, y, z, FRAME_BLOCK))
    world.append(Block(x + 3, y, z, FRAME_BLOCK))
    # 红石线
    world.append(Block(x + 0, y + 1, z, REDSTONE_WIRE))
    # 红石中继器
    world.append(Block(x + 1, y + 1, z, REPEATER, delay=int(1 + gt % 8 / 2), facing="west"))
    # 粘性活塞
    world.append(Block(x + 2, y + 1, z, STICKY_PISTON, facing="up"))
    # 树干和树叶
    world.append(Block(x + 2, y + 2, z, TREE_LOG))
    world.append(Block(x + 1, y + 3, z, TREE_LEAVES))
    # 为了clear指令在活塞推出的情况下也能奏效
    world.append(Block(x + 2, y + 3, z, "air"))
    # 第一个音符盒 及其 音色方块 (x更大的,也就是东侧的那个)
    pitch_, base_block = get_pitch_and_base(first_pitch)
    if pitch_ and base_block:
        world.append(Block(x + 3, y + 5, z, NOTE_BLOCK, pitch=pitch_))
        world.append(Block(x + 3, y + 4, z, base_block))
    # 第二个音符盒 及其 音色方块
    pitch_, base_block = get_pitch_and_base(second_pitch)
    if pitch_ and base_block:
        world.append(Block(x + 0, y + 5, z, NOTE_BLOCK, pitch=pitch_))
        world.append(Block(x + 0, y + 4, z, base_block))
    # 给音符盒充能的两个方块
    world.append(Block(x + 1, y + 5, z, FRAME_BLOCK))
    world.append(Block(x + 2, y + 5, z, FRAME_BLOCK))
    # 侦测器
    world.append(Block(x + 1, y + 4, z, OBSERVER, facing="down"))
    world.append(Block(x + 2, y + 4, z, OBSERVER, facing="down"))

# 向world添加一个偶Unit
def build_even(x, y, z, world, gt, first_note=None, second_note=None):
    first_pitch = first_note.pitch if first_note else None
    second_pitch = second_note.pitch if second_note else None
    # 结构方块
    world.append(Block(x + 0, y, z, FRAME_BLOCK))
    world.append(Block(x + 1, y, z, FRAME_BLOCK))
    world.append(Block(x + 3, y, z, FRAME_BLOCK))
    # 红石线
    world.append(Block(x + 0, y + 1, z, REDSTONE_WIRE))
    # 红石中继器
    world.append(Block(x + 1, y + 1, z, REPEATER, delay=int(1 + gt % 8 / 2), facing="west"))
    # 粘性活塞
    world.append(Block(x + 2, y + 0, z, STICKY_PISTON, facing="up"))
    # 树干和树叶
    world.append(Block(x + 2, y + 1, z, TREE_LOG))
    world.append(Block(x + 1, y + 2, z, TREE_LEAVES))
    # 为了clear指令在活塞推出的情况下也能奏效
    world.append(Block(x + 2, y + 2, z, "air"))
    # 第一个音符盒 及其 音色方块 (x更大的,也就是东侧的那个)
    pitch_, base_block = get_pitch_and_base(first_pitch)
    if pitch_ and base_block:
        world.append(Block(x + 3, y + 4, z, NOTE_BLOCK, pitch=pitch_))
        world.append(Block(x + 3, y + 3, z, base_block))
    # 第二个音符盒 及其 音色方块
    pitch_, base_block = get_pitch_and_base(second_pitch)
    if pitch_ and base_block:
        world.append(Block(x + 0, y + 4, z, NOTE_BLOCK, pitch=pitch_))
        world.append(Block(x + 0, y + 3, z, base_block))
    # 给音符盒充能的两个方块
    world.append(Block(x + 1, y + 4, z, FRAME_BLOCK))
    world.append(Block(x + 2, y + 4, z, FRAME_BLOCK))
    # 侦测器
    world.append(Block(x + 1, y + 3, z, OBSERVER, facing="down"))
    world.append(Block(x + 2, y + 3, z, OBSERVER, facing="down"))

# 向world添加一个间隔Unit for L
def build_gap_L(x, y, z, world):
    world.append(Block(x + 0, y, z, FRAME_BLOCK))
    world.append(Block(x + 0, y + 1, z, REPEATER, facing="south", delay=4))

# 向world添加一个间隔Unit for R
def build_gap_R(x, y, z, world):
    world.append(Block(x + 0, y, z, FRAME_BLOCK))
    world.append(Block(x + 0, y + 1, z, REPEATER, facing="north", delay=4))


world = []

for i, bar in enumerate(bars_L):
    # 该小节对应的中间结构框架
    for dx in range(5):                                             # 5个结构块
        world.append(Block(X + i * 5 + dx, Y, Z, FRAME_BLOCK))
    world.append(Block(X + i * 5 + 0, Y, Z - 1, FRAME_BLOCK))       # 1个结构块 (!这里的Z-1在右侧是Z+1!)
    world.append(Block(X + i * 5 + 0, Y + 1, Z - 1, REDSTONE_WIRE)) # 1个红石线 (!这里的Z-1在右侧是Z+1!)
    world.append(Block(X + i * 5 + 0, Y + 1, Z, REDSTONE_WIRE))     # 1个红石线
    for dx in range(1,5):                                           # 4个中继器
        world.append(Block(X + i * 5 + dx, Y + 1, Z, REPEATER, delay=4, facing="west"))

    # 该小节的所有Unit()
    build_x, build_y, build_z = X + i * 5 + 0, Y, Z - 1     # (!这里的Z-1在右侧是Z+1!)
    for unit in bar:
        build_z -= 1            # (!这里的Z-1在右侧是Z+1!)
        # print(unit)
        if unit.type == 0:      # 偶单元
            build_odd(build_x, build_y, build_z, world, unit.get_gt(), unit.first_note, unit.second_note)
        elif unit.type == 1:    # 奇单元
            build_even(build_x, build_y, build_z, world, unit.get_gt(), unit.first_note, unit.second_note)
        else:                   # 中继器
            build_gap_L(build_x, build_y, build_z, world)

for i, bar in enumerate(bars_R):
    world.append(Block(X + i * 5 + 0, Y, Z + 1, FRAME_BLOCK))       # 1个结构块 (!这里的Z-1在右侧是Z+1!)
    world.append(Block(X + i * 5 + 0, Y + 1, Z + 1, REDSTONE_WIRE)) # 1个红石线 (!这里的Z-1在右侧是Z+1!)

    # 该小节的所有Unit()
    build_x, build_y, build_z = X + i * 5 + 0, Y, Z + 1             # (!这里的Z-1在右侧是Z+1!)
    for unit in bar:
        build_z += 1            # (!这里的Z-1在右侧是Z+1!)
        # print(unit)
        if unit.type == 0:      # 偶单元
            build_odd(build_x, build_y, build_z, world, unit.get_gt(), unit.first_note, unit.second_note)
        elif unit.type == 1:    # 奇单元
            build_even(build_x, build_y, build_z, world, unit.get_gt(), unit.first_note, unit.second_note)
        else:                   # 中继器
            build_gap_R(build_x, build_y, build_z, world)



# 构造指令[build_ID.mcfunction]
with open(FUNCTION_FOLDER + f"build_{0}.mcfunction", "w") as f:

    # 为 world 中的 Block实例 生成 setblock 指令
    for block in world:
        if block.block_type == NOTE_BLOCK:
            pitch_0_25 = block.info['pitch']
            print(f"setblock {block.x} {block.y} {block.z} note_block[note={pitch_0_25}]", file=f)
        elif block.block_type == REPEATER:
            print(f"setblock {block.x} {block.y} {block.z} repeater[facing={block.info['facing']}, delay={block.info['delay']}]", file=f)
        elif block.block_type == OBSERVER:
            print(f"setblock {block.x} {block.y} {block.z} observer[facing={block.info['facing']}]", file=f)
        elif block.block_type == STICKY_PISTON:
            print(f"setblock {block.x} {block.y} {block.z} sticky_piston[facing={block.info['facing']}]", file=f)
        elif block.block_type == TREE_LEAVES:
            print(f"setblock {block.x} {block.y} {block.z} {TREE_LEAVES}[persistent = true]", file=f)
        else:
            print(f"setblock {block.x} {block.y} {block.z} {block.block_type}",file=f)


# 析构指令[clear_ID.mcfunction]
with open(FUNCTION_FOLDER + f"clear_{0}.mcfunction", "w") as f:
    for block in world:
        print(f"setblock {block.x} {block.y} {block.z} air replace", file=f)

        
