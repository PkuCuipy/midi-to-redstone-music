#================================#
#======  PART-0 宏/类/函数  ======#
#================================#

# >>>>>>>>>>>> 本文件需要调整的部分 >>>>>>>>>>>>

# 设置"建造原点"坐标, 默认为(0,64,0)
X, Y, Z = 0, 64, 0

# 设置midi的小节数量上限
BAR_AMOUNT = 99

# 待读取的midi文件名(.mid后缀不可省略)
MIDI_FILE_NAME = "CaoCao (by JJ Lin).mid"

# 改成[你自己的]Minecraft存档的路径(最后 不要 加上"/")
# 强调: 这里是我自己的游戏路径, 请改成你自己的
MINECRAFT_SAVE_PATH = "/Users/cuipy/Library/Application Support/minecraft/saves/rsm_demo"

# <<<<<<<<<<<< 可调整部分结束 <<<<<<<<<<<<


# 通过存档路径计算function路径
FUNCTION_FOLDER = MINECRAFT_SAVE_PATH + "/datapacks/rsm/data/rsm/functions/"

# 移调相关: 把针对不同乐器的 midi_pitch 映射到[0-24]
# 注意: 请自己确保midi音符符合该乐器的音域要求!
PITCH_DELTA = {
    "bass":-42,
    "didgeridoo": -42,
    "guitar": -54,
    "pling": -66,
    "bit": -66,
    "banjo": -66,
    "harp": -66,
    "iron_xylophone": -66,
    "cow_bell": -78,
    "flute": -78,
    "xylophone": -90,
    "chime": -90,
    "bell": -90,
    "bassdrum": -35,
    "snare": -36,
    "hat": -37
}

# 音色对应的底部方块
BASE_BLOCK = {
    "bass": "oak_planks",
    "didgeridoo": "pumpkin",
    "guitar": "white_wool",
    "pling": "glowstone",
    "bit": "emerald_block",
    "banjo": "hay_block",
    "harp": "dirt",
    "iron_xylophone": "iron_block",
    "cow_bell": "soul_sand",
    "flute": "clay",
    "xylophone": "bone_block",
    "chime": "packed_ice",
    "bell": "gold_block",
    "bassdrum": "stone",
    "snare": "sand",
    "hat": "glass"
}

# 通过音高区分鼓件
DRUM_NAME_BY_PITCH = {
    36: "bassdrum",
    37: "snare",
    38: "hat"
}

# 一些用到的方块宏定义
FRAME_BLOCK = "yellow_concrete"     # 框架方块1
DEBUG_BLOCK = "red_concrete"        # 框架方块2
CONNECT_NODE = "redstone_wire"      # 主轴连接用
NOTE_BLOCK = "note_block"           # 音符盒
PRE_BLOCK = "redstone_lamp"         # 前置在音符盒前, 传递中继器信号的方块
REPEATER = "repeater"               # 中继器
REDSTONE_WIRE = "redstone_wire"     # 红石线


# minecraft原生支持的 BPM / 单位长度
# 其余的速度都有可能导致四舍五入, 造成节奏错乱!
# 具体而言, 由于 redstone_tick 固定为0.1s, 速度信息是不可修改的.
# 而此红石工程的最小音乐单位因此固定为0.1s.
# 其实这个工程还有扩充的可能:
# - 首先, 很多乐器是可以共享充能方块的, 借此增加容纳的音符数
# (事实上只要这个乐器的BASE_BLOCK是非透明方块就行)
# 但目前好像没有必要这么做...也主要是程序实现起来可能会麻烦一点
# - 其次, 可以相隔1tick(0.05s)激活两套RSM设备, 使得最小单位变为0.05s (1 game_tick)
MIDI_BPM = 150
SEMIQUAVER_SEC = 0.1


class Note:
    def __init__(self, bar, which, qpos, spos, pitch, instrument, is_drums, drum_name):
        # 设置bar和which是为了直观表示某个音符的"时间轴位置"
        # 设置qpos和spos是为了方便后面计算"world位置"...
        self.bar = bar      # 第几个"小节"                           从0开始
        self.which = which  # 该小节的第几个"16分音符"                从0到3
        self.qpos = qpos    # 该小节的第几个"4分音符(quarter)"        从0到3
        self.spos = spos    # 该4分音符的第几个"16分音符(semiquaver)"  从0到3
        self.pitch = pitch  # 音符的标准绝对音高                      不是mc的[0,24]那个
        self.instrument = instrument   # 该音符对应乐器名
        self.is_drums = is_drums
        self.drum_name = drum_name
    def __repr__(self):
        return f"Note({self.instrument}-{self.bar}-{self.qpos}-{self.spos}: {self.pitch})"


class Beat: # (1Beat = 1四分音符)
    def __init__(self, which):
        self.which = which
        self.notes = []
        self.note_count = 0

    def __getitem__(self, idx):
        return self.notes[idx]

    def append(self, item):
        self.notes.append(item)
        self.note_count += 1


class Bar:
    def __init__(self, which, channel_name):
        self.which = which
        self.channel_name = channel_name
        self.beats = [Beat(i) for i in range(4)]
    def __repr__(self):
        return f"声道:{self.channel_name}; 小节编号:{self.which}"
    def __getitem__(self, idx):
        return self.beats[idx]


class Block:
    def __init__(self, x, y, z, block_type, **info):
        self.x, self.y, self.z = x, y, z
        self.block_type = block_type
        self.info = info


# 四舍五入到最近的"十分位", 并在舍入超出阈值时发出警告
# 用于处理float的精度问题,
# 或者用于 对速度不匹配的.midi进行近似
def round(x):
    as_return = int(10 * x + 0.5) / 10
    if abs(x-as_return) > 0.04:
        # print(f"Warning: 产生了一个节奏显著错位的音符(误差={x-as_return}s)")
        pass
    return int(x+0.5)

