import pretty_midi
from utils import *
from mc_block_gen import *

"""
1rt版本介绍:
    制作日期: 2020.8.2 ~ 2020.8.6
    
    功能: 读入指定格式的.mid文件, 生成对应的红石音乐机器
    
    工程各个文件(part)的功能:
        part0:  用户为程序提供的必要信息(在注释中有提示) [用户需要针对性自行修改]
                程序运行所需的宏定义  [除非你清楚自己在做什么, 否则不要修改] 
        part1:  读入.mid文件, 把每个音符格式化到近邻的0.1s, 得到的数据送入part2_and_part3  [除非你清楚自己在做什么, 否则不要修改]
        part2:  接受part1传入的音符数据, 把每个音符转化成对应的方块信息, 完成后将数据传入part3
        part3:  接受part2传入的方块数据, 生成.mcfunction文件, 其中为对应方块的setblock指令
        
    !!!使用方法: 
        0. 安装python3.8, 并安装 pretty_midi 库.
        1. 打开part0.py文件, 按照其中注释修改part0.py文件 并保存.
        2. 打开游戏的那个存档, 输入 /function , 敲空格, 不出意外的话游戏就会给出指令提示.
        4. rsm:build 开头的指令是建造相关; rsm:clear 开头的指令是把这部分恢复为空气
        5. rsm:clear指令可能会生成大量掉落物造成卡顿, 输入 /kill @e[type=item] 可以删除全部掉落物.
    
    1rt版本局限性:
        正如版本名所言, 其中 1rt 表示 1 红石刻(redstonetick), 即 0.1 秒, 也就是说本工程支持的最小时间精度为0.1s,
        所有音符都会被舍入到最近的那个0.1上面去, 
        所以[除非]您的音乐的速度为[150bpm(的十六分音符)],
        否则都会有由于舍入而造成的时间误差.
        之所以是0.1s, 是因为在Minecraft中, 红石的更新/传递需要时间,
        而这个时间恰好为0.1s
        不过,
        事实上, Minecraft还有一个更小的时间间隔, 叫做 游戏刻(gametick),
        它的时间间隔为0.05s
        也就是红石刻的1/2
        采用"树电"等方法可以让红石音乐的最小时间间隔缩小到此版本的一半!
        不过由于需要采用树电, 
        会面临许多局限.
        比如由于活塞的介入, 听歌时需要关闭方块音效.
        此外, 机器的体积也会有所增加.
        1gt版本我在之后也许会制作!
    
"""


#=============================================#
#====== PART-0.9 创建/function的运行环境   =====#
#=============================================#

import os
try:
    os.makedirs(MINECRAFT_SAVE_PATH + "/datapacks/rsm/data/rsm/functions")
except FileExistsError:
    # print("此目录已存在, 不再重复创建")
    pass

with open(MINECRAFT_SAVE_PATH + "/datapacks/rsm/pack.mcmeta", 'w') as f:
    print("""{"pack":{"pack_format":4,"description":"redstone_functions"}}""", end='', file=f)



#================================#
#====== PART-1 读取MIDI文件 ======#
#================================#

# 读取文件为PrettyMIDI格式
midi_data = pretty_midi.PrettyMIDI(MIDI_FILE_NAME)


# 一对一对地(L 和 R)遍历.midi文件的所有channel
for instrument_idx in range(0, int(len(midi_data.instruments) / 2)):

    # 存储当前乐器 [左/右声道] 的所有 [小节(Bar类的类实例)] 的 [列表(list)] 组成的字典(用字典只是为了LR共用代码)
    bars = dict()
    bars['L'] = [Bar(i, 'L') for i in range(BAR_AMOUNT)]
    bars['R'] = [Bar(i, 'R') for i in range(BAR_AMOUNT)]

    # 确保文件命名符合规范
    assert midi_data.instruments[2 * instrument_idx].name[-1] == 'L'
    assert midi_data.instruments[2 * instrument_idx + 1].name[-1] == 'R'
    assert midi_data.instruments[2 * instrument_idx].name[0:-1] == midi_data.instruments[2 * instrument_idx + 1].name[0:-1]

    # 一次读取两个乐器, 虽然s在midi中是两个乐器, 但其实是一个音色的两个声道
    instruments = dict()
    instruments['L'] = midi_data.instruments[2 * instrument_idx]
    instruments['R'] = midi_data.instruments[2 * instrument_idx + 1]
    instrument_name = instruments['L'].name[:-1]   # 乐器名(去掉L/R后缀了)

    for LorR in ['L', 'R']:
        for note in instruments[LorR].notes:
            total_which = round(note.start / SEMIQUAVER_SEC)    # 在整个时间线的位置
            bar_ = total_which // 16                            # 在哪个小节
            which_ = total_which % 16                           # 在这个小节的第几个十六分音符
            qpos_ = which_ // 4                                 # 在这个小节的第几个四分音符(quarter)
            spos_ = which_ % 4                                  # 在这个四分音符的第几个十六分音符(semiquaver)
            pitch_ = note.pitch                                 # 音符的标准绝对音高
            # 当前载入的乐器是否为鼓组(drums)
            is_drums_ = True if instrument_name == "drums" else False
            drum_name_ = DRUM_NAME_BY_PITCH[note.pitch] if is_drums_ else None
            # bars_L 的第 bar_ 小节, 的第 qpos_ 拍, 新增一个音符
            bars[LorR][bar_][qpos_].append(Note(bar_, which_, qpos_, spos_, pitch_, instrument_name, is_drums_, drum_name_))

    # 将LR的midi数据传递给Part2和Part3进行后续操作
    part2_and_part3(instrument_idx, instrument_name, X, Y + instrument_idx * 4, Z, bars['L'], bars['R'], FUNCTION_FOLDER)




