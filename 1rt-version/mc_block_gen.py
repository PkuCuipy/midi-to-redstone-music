from utils import *

def part2_and_part3(instrument_index, instrument_name, x, y, z, bars_L, bars_R, function_folder):
    '''
    :param instrument_index:    该midi中的第几个乐器? (乐器,而非声道!)
    :param instrument_name:     当前乐器名
    :param x, y, z:             该乐器的"建造原点"
    :param bars_L:              L声道的所有小节数据
    :param bars_R:              R声道的所有小节数据
    :param function_folder:     生成的.mcfunction文件放在哪?
    '''

    #================================#
    #====== PART-2 内存虚拟建造 ======#
    #================================#

    world = dict()

    # [主轴框架]
    for dx in range(0, BAR_AMOUNT * 5):     # 框架方块
        world[(x + dx, y, z)] = Block(x + dx, y, z, DEBUG_BLOCK)
    for dx in range(0, BAR_AMOUNT):         # 4个中继器
        world[(x + 5 * dx + 1, y + 1, z)] = Block(x + 5 * dx + 1, y + 1, z, REPEATER, delay=4, facing="west")
        world[(x + 5 * dx + 2, y + 1, z)] = Block(x + 5 * dx + 2, y + 1, z, REPEATER, delay=4, facing="west")
        world[(x + 5 * dx + 3, y + 1, z)] = Block(x + 5 * dx + 3, y + 1, z, REPEATER, delay=4, facing="west")
        world[(x + 5 * dx + 4, y + 1, z)] = Block(x + 5 * dx + 4, y + 1, z, REPEATER, delay=4, facing="west")
    for dx in range(0, BAR_AMOUNT):         # 连接点: 红石线/红石灯 (后者可以"显示播放头" 但阻碍中间行走)
        world[(x + 5 * dx, y + 1, z)] = Block(x + 5 * dx, y + 1, z, CONNECT_NODE)
    for dx in range(0, BAR_AMOUNT):         # 连接主轴和支线的红石线及其底座
        world[(x + dx * 5, y + 0, z + 1)] = Block(x + dx * 5, y + 0, z + 1, FRAME_BLOCK)
        world[(x + dx * 5, y + 1, z + 1)] = Block(x + dx * 5, y + 1, z + 1, REDSTONE_WIRE)
        world[(x + dx * 5, y + 0, z - 1)] = Block(x + dx * 5, y + 0, z - 1, FRAME_BLOCK)
        world[(x + dx * 5, y + 1, z - 1)] = Block(x + dx * 5, y + 1, z - 1, REDSTONE_WIRE)


    # [侧框架和音符盒相关]

    # 每一拍最多容纳音符数, 最大为14(受当前架构中红石线传递距离限制)
    # 你需要自己确保每一拍不会有更多的音符, 因为多出来的会被直接舍弃
    # 此外, 基于当前架构, 如果某个小节的音符太多,
    # 那么远处的音符(对应于每小节的第三拍和第四拍)会很小声, 甚至听不到,
    MAX_NOTES_PER_BEATS = 14

    # 注:
    # 下面的代码分别用于生成L和R的部分
    # 事实上L和R的代码只有很小的差别,
    # 但如果想让L和R共用代码,
    # 目前我只能想到是用 bars['L'] bars['R']
    # 这样的字典来写
    # 但方括号太多的话, 可读性很差
    # 不知道有没有更高级的方法

    for i in range(BAR_AMOUNT):     # R
        dz = 1
        for beats_index in range(4):
            for note in bars_L[i].beats[beats_index].notes[0:min(MAX_NOTES_PER_BEATS, len(bars_L[i].beats[beats_index].notes))]:
                dz += 1
                # 决定音符盒的音高 以及底部音色方块类型
                if instrument_name == "drums":
                    base_block = BASE_BLOCK[DRUM_NAME_BY_PITCH[note.pitch]]
                    pitch_0_25 = note.pitch + PITCH_DELTA[DRUM_NAME_BY_PITCH[note.pitch]]
                    assert pitch_0_25 in range(0, 25)
                else:
                    base_block = BASE_BLOCK[instrument_name]
                    pitch_0_25 = note.pitch + PITCH_DELTA[instrument_name]
                    assert pitch_0_25 in range(0, 25)

                world[(x + i * 5 + 3, y + 0, z + dz)] = Block(x + i * 5 + 3, y + 0, z + dz, base_block)  # 底部音色方块
                if base_block == "sand": world[(x + i * 5 + 3, y - 1, z + dz)] = Block(x + i * 5 + 3, y - 1, z + dz, DEBUG_BLOCK)   # 防止sand下坠
                world[(x + i * 5 + 3, y + 1, z + dz)] = Block(x + i * 5 + 3, y + 1, z + dz, NOTE_BLOCK, pitch=pitch_0_25)  # 音符盒
                world[(x + i * 5 + 2, y + 1, z + dz)] = Block(x + i * 5 + 2, y + 1, z + dz, PRE_BLOCK)      # 充能方块
                world[(x + i * 5 + 1, y + 0, z + dz)] = Block(x + i * 5 + 1, y + 0, z + dz, FRAME_BLOCK)    # 精细中继器底座
                world[(x + i * 5 + 1, y + 1, z + dz)] = Block(x + i * 5 + 1, y + 1, z + dz, REPEATER, facing="west", delay=note.spos + 1)   # 精细中继器
                world[(x + i * 5 + 0, y + 0, z + dz)] = Block(x + i * 5 + 0, y + 0, z + dz, FRAME_BLOCK)    # 红石线底座
                world[(x + i * 5 + 0, y + 1, z + dz)] = Block(x + i * 5 + 0, y + 1, z + dz, REDSTONE_WIRE)  # 红石线
            dz += 1
            if beats_index != 3:
                world[(x + i * 5 + 0, y + 0, z + dz)] = Block(x + i * 5, y + 0, z + dz, FRAME_BLOCK)        # 节拍间中继器底座
                world[(x + i * 5 + 0, y + 1, z + dz)] = Block(x + i * 5, y + 1, z + dz, REPEATER, facing="north", delay=4)      # 节拍间中继器

    for i in range(BAR_AMOUNT):     # L
        dz = -1
        for beats_index in range(4):
            for note in bars_R[i].beats[beats_index].notes[0:min(MAX_NOTES_PER_BEATS, len(bars_R[i].beats[beats_index].notes))]:
                dz -= 1
                # 决定音符盒的音高 以及底部音色方块类型
                if instrument_name == "drums":
                    base_block = BASE_BLOCK[DRUM_NAME_BY_PITCH[note.pitch]]
                    pitch_0_25 = note.pitch + PITCH_DELTA[DRUM_NAME_BY_PITCH[note.pitch]]
                    assert pitch_0_25 in range(0, 25)
                else:
                    base_block = BASE_BLOCK[instrument_name]
                    pitch_0_25 = note.pitch + PITCH_DELTA[instrument_name]
                    assert pitch_0_25 in range(0, 25)

                world[(x + i * 5 + 3, y + 0, z + dz)] = Block(x + i * 5 + 3, y + 0, z + dz, base_block)     # 底部音色方块
                if base_block == "sand": world[(x + i * 5 + 3, y - 1, z + dz)] = Block(x + i * 5 + 3, y - 1, z + dz, DEBUG_BLOCK)  # 防止sand下坠
                world[(x + i * 5 + 3, y + 1, z + dz)] = Block(x + i * 5 + 3, y + 1, z + dz, NOTE_BLOCK, pitch=pitch_0_25)  # 音符盒
                world[(x + i * 5 + 2, y + 1, z + dz)] = Block(x + i * 5 + 2, y + 1, z + dz, PRE_BLOCK)      # 充能方块
                world[(x + i * 5 + 1, y + 0, z + dz)] = Block(x + i * 5 + 1, y + 0, z + dz, FRAME_BLOCK)    # 精细中继器底座
                world[(x + i * 5 + 0, y + 0, z + dz)] = Block(x + i * 5 + 0, y + 0, z + dz, FRAME_BLOCK)    # 红石线底座
                world[(x + i * 5 + 0, y + 1, z + dz)] = Block(x + i * 5 + 0, y + 1, z + dz, REDSTONE_WIRE)  # 红石线
                world[(x + i * 5 + 1, y + 1, z + dz)] = Block(x + i * 5 + 1, y + 1, z + dz, REPEATER, facing="west", delay=note.spos + 1)   # 精细中继器
            dz -= 1
            if beats_index != 3:
                world[(x + i * 5 + 0, y + 0, z + dz)] = Block(x + i * 5, y + 0, z + dz, FRAME_BLOCK)        # 节拍间中继器底座
                world[(x + i * 5 + 0, y + 1, z + dz)] = Block(x + i * 5, y + 1, z + dz, REPEATER, facing="south", delay=4)      # 节拍间中继器


    #=====================================#
    #====== PART-3 生成Minecraft指令 ======#
    #=====================================#

    # 构造指令[build_ID.mcfunction]
    with open(function_folder + f"build_{instrument_index}.mcfunction", "w") as f:

        # 为 world 中的 Block实例 生成 setblock 指令
        for pos, block in world.items():
            if block.block_type == NOTE_BLOCK:
                pitch_0_25 = block.info['pitch']
                print(f"setblock {pos[0]} {pos[1]} {pos[2]} note_block[note={pitch_0_25}]", file=f)
            elif block.block_type == REPEATER:
                print(f"setblock {pos[0]} {pos[1]} {pos[2]} repeater[facing={block.info['facing']}, delay={block.info['delay']}]", file=f)
            else:
                print(f"setblock {pos[0]} {pos[1]} {pos[2]} {block.block_type}",file=f)


    # 析构指令[clear_ID.mcfunction]
    with open(function_folder + f"clear_{instrument_index}.mcfunction", "w") as f:
        for pos in world.keys():
            print(f"setblock {pos[0]} {pos[1]} {pos[2]} air replace", file=f)


