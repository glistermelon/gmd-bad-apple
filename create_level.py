from process_video import *
from gmdify import gmdify

PX_SIZE = (30 * 27 / 384)
PX_SCALE = PX_SIZE / (30 / 4 * 4)
BORDER_TOP = 27 * 30
FPS = 30
SEQ_LOAD = 1000 # 1000 frames per sequence

class Object():
    def __init__(self, id, x = 0, y = 0, *, scale_x = 1, scale_y = 1):
        self.id = id
        self.x = x
        self.y = y
        self.scale_x = scale_x
        self.scale_y = scale_y
        self.group_id = None
        self.attrs = {}
    def __str__(self):
        s = f"1,{self.id},2,{self.x},3,{self.y},155,1"
        if self.group_id is not None:
            s += f",33,{self.group_id}"
        s += ''.join(f",{k},{v}" for k, v in self.attrs.items())
        return s + ';'

class Pixel(Object):
    def __init__(self): # 211 or 917 usually
        super(Pixel, self).__init__(211, scale_y = 0.28125)

class SequenceAbstract():
    def __init__(self):
        self.ops = []
    def add_op(self, move_x, move_y, scale_x):
        self.ops.append((move_x, move_y, scale_x))
    def add_no_op(self):
        self.ops.append(None)

DUMMY_X_GID = 1
DUMMY_Y_GID = 2
NO_OP_GID = 3
RESET_MOVE_GID = 4 # Don't change! There's a trigger that I put in the input gmd file that aligns this one, and it is hardcoded to this group id.
INIT_GID = 5       # same here
INV_COLOR_1 = 6    # same here
INV_COLOR_2 = 7    # same here
DEFAULT_GID = 8
group_id_counter = DEFAULT_GID

END_GID = 9994 # more hardcoding yay

class Trigger(Object):
    def __init__(self, *args, **kwargs):
        super(Trigger, self).__init__(*args, **kwargs)
        self.spawn_trigger = False
        self.multi_trigger = False
    def __str__(self):
        if self.spawn_trigger: self.attrs[62] = 1
        if self.multi_trigger: self.attrs[87] = 1
        return Object.__str__(self = self)

class Follow(Trigger):
    def __init__(self, *, target_id, follow_id, x = 0, y = 0):
        super(Follow, self).__init__(1347)
        self.mod_x = x
        self.mod_y = y
        self.target_id = target_id
        self.follow_id = follow_id
    def __str__(self):
        self.attrs[72] = self.mod_x
        self.attrs[73] = self.mod_y
        self.attrs[51] = self.target_id
        self.attrs[71] = self.follow_id
        return Trigger.__str__(self = self)

class Scale(Trigger):
    def __init__(self, x, *, target_id, inverse = False):
        super(Scale, self).__init__(2067)
        self.scale_x = x
        self.target_id = target_id
        self.inverse = inverse
    def __str__(self):
        self.attrs[150] = self.scale_x
        self.attrs[51] = self.target_id
        if self.inverse: self.attrs[153] = 1
        return Trigger.__str__(self = self)

class Move(Trigger):
    def __init__(self, *, target_id, x = 0, y = 0):
        super(Move, self).__init__(901)
        self.move_x = x
        self.move_y = y
        self.target_id = target_id
    def __str__(self):
        self.attrs[28] = self.move_x * 3
        self.attrs[29] = self.move_y * 3
        self.attrs[51] = self.target_id
        return Trigger.__str__(self = self)

class Sequence(Trigger):
    def __init__(self):
        super(Sequence, self).__init__(3607)
        self.targets = []
    def __str__(self):
        s = ''
        for i in range(0, len(self.targets), SEQ_LOAD):
            targets = self.targets[i : i + SEQ_LOAD]
            if i != 0:
                targets.insert(0, [NO_OP_GID, sum(t[1] for t in self.targets[:i])])
            self.attrs[435] = '.'.join([f'{t[0]}.{t[1]}' for t in targets])
            Sequence.nums += len(targets) * 2
            s += Trigger.__str__(self = self)
        return s
    def add_target(self, target_id, count = 1):
        if len(self.targets) == 0 or self.targets[-1][0] != target_id:
            self.targets.append([target_id, count])
        else:
            self.targets[-1][1] += count
Sequence.nums = 0

class Spawn(Trigger):
    def __init__(self, target_id, *, delay = None, remap = None):
        super(Spawn, self).__init__(1268)
        self.target_id = target_id
        self.delay = delay
        self.remap = remap
    def __str__(self):
        self.attrs[51] = self.target_id
        if self.delay: self.attrs[63] = self.delay
        if self.remap: self.attrs[442] = '.'.join(str(i) for p in self.remap.items() for i in p)
        return Trigger.__str__(self = self)

frames = get_frames("bad apple.mp4")

objects = []

for _ in range(max(len(frame["runs"]) for frame in frames)):
    obj = Pixel()
    obj.sequence = SequenceAbstract()
    obj.group_id = group_id_counter
    group_id_counter += 1
    obj.attrs[64] = 1 # don't fade
    obj.attrs[67] = 1 # don't enter
    objects.append(obj)

inv_color_seq = Sequence()
inv_color_seq.spawn_trigger = True
inv_color_seq.multi_trigger = True
invert_state = True

for i in range(0, len(frames), 30 // FPS):
    frame = frames[i]

    if frame["invert"]:
        inv_color_seq.add_target(INV_COLOR_1 if invert_state else INV_COLOR_2)
        invert_state = not invert_state
    else:
        inv_color_seq.add_target(NO_OP_GID)

    runs = frame["runs"]
    used = []
    for run in runs:
        obj = objects.pop()
        obj.sequence.add_op(run.x, run.y, run.len)
        obj.attrs[128] = PX_SCALE
        obj.attrs[129] = PX_SCALE * 1.1
        used.append(obj)
    for obj in objects:
        obj.sequence.add_no_op()
    objects += used

move_x_trigs = {}
for x in set(run.x for frame in frames for run in frame['runs']):
    trig = Follow(target_id = DEFAULT_GID, follow_id = DUMMY_X_GID, x = PX_SIZE * x / 3)

    trig.group_id = group_id_counter
    group_id_counter += 1
    trig.spawn_trigger = True
    trig.multi_trigger = True

    move_x_trigs[x] = trig

move_y_trigs = {}
for y in set(run.y for frame in frames for run in frame['runs']):
    trig = Follow(target_id = DEFAULT_GID, follow_id = DUMMY_Y_GID, y = BORDER_TOP - PX_SIZE * y / 3)

    trig.group_id = group_id_counter
    group_id_counter += 1
    trig.spawn_trigger = True
    trig.multi_trigger = True

    move_y_trigs[y] = trig

scale_trigs = {}
inv_scale_trigs = []
extra_inv_scale_trigs = []
spawn_inv_scale_trigs = []
for scale in set(run.len for frame in frames for run in frame['runs']):
    trig = Scale(scale, target_id = DEFAULT_GID)
    inv_trig = Scale(scale, target_id = DEFAULT_GID, inverse = True)

    trig.group_id = group_id_counter
    inv_trig.group_id = group_id_counter + 1
    group_id_counter += 2
    trig.spawn_trigger = True
    trig.multi_trigger = True
    inv_trig.spawn_trigger = True
    inv_trig.multi_trigger = True

    if inv_trig.scale_x > 100:
        extra_trig = Scale(100, target_id = DEFAULT_GID, inverse = True)
        inv_trig.scale_x /= 100
        extra_trig.group_id = inv_trig.group_id
        extra_trig.spawn_trigger = True
        extra_trig.multi_trigger = True
        extra_inv_scale_trigs.append(extra_trig)

    scale_trigs[scale] = trig

    inv_spawn = Spawn(inv_trig.group_id, delay = 1 / FPS)
    inv_spawn.group_id = trig.group_id
    inv_spawn.spawn_trigger = True
    inv_spawn.multi_trigger = True
    spawn_inv_scale_trigs.append(inv_spawn)
    inv_scale_trigs.append(inv_trig)

INIT_SEQS_GID = group_id_counter
group_id_counter += 1

#######################################################

sequence_spawners = []
sequences = []

reset_move = Object(901)
reset_move.group_id = RESET_MOVE_GID
reset_move.attrs[51] = DEFAULT_GID
reset_move.attrs[71] = RESET_MOVE_GID
reset_move.attrs[100] = 1 # enable target mode
reset_move.attrs[395] = DEFAULT_GID
reset_move.attrs[62] = 1 # spawn trigger
reset_move.attrs[87] = 1 # multi trigger
reset_move_groups = []

for obj in objects:
    seq_move_x = Sequence()
    seq_move_y = Sequence()
    seq_scale = Sequence()
    for trig in (seq_move_x, seq_move_y, seq_scale):
        trig.spawn_trigger = True
        trig.multi_trigger = True
        trig.group_id = group_id_counter
    reset_move_groups.append(group_id_counter)
    for op in obj.sequence.ops:
        if op is None:
            seq_move_x.add_target(NO_OP_GID)
            seq_move_y.add_target(NO_OP_GID)
            seq_scale.add_target(NO_OP_GID)
            continue
        seq_move_x.add_target(move_x_trigs[op[0]].group_id)
        seq_move_y.add_target(move_y_trigs[op[1]].group_id)
        seq_scale.add_target(scale_trigs[op[2]].group_id)
    spawn = Spawn(group_id_counter, remap = { DEFAULT_GID : obj.group_id })
    spawn.spawn_trigger = True
    spawn.multi_trigger = True
    spawn.group_id = INIT_SEQS_GID

    sequence_spawners.append(spawn)
    sequences.append(seq_move_x)
    sequences.append(seq_move_y)
    sequences.append(seq_scale)

    group_id_counter += 1

extra_spawns = []
while len(reset_move_groups):
    spawn = Spawn(reset_move.group_id)
    spawn.spawn_trigger = True
    spawn.multi_trigger = True
    spawn.attrs[57] = '.'.join([str(n) for n in reset_move_groups[:10]])
    del reset_move_groups[:10]
    extra_spawns.append(spawn)

#######################################################
    
inv_color_seq.group_id = INIT_SEQS_GID

loop1 = Spawn(INIT_SEQS_GID)
loop1.group_id = group_id_counter
group_id_counter += 1
loop2 = Spawn(loop1.group_id, delay = 1 / FPS)
loop2.group_id = INIT_SEQS_GID

loop1.spawn_trigger = True
loop1.multi_trigger = True
loop2.spawn_trigger = True
loop2.multi_trigger = True

loop1.attrs[57] = INIT_GID

dummy_x = Object(5, 0, 0)
dummy_x.group_id = DUMMY_X_GID

dummy_y = Object(5, 0, 0)
dummy_y.group_id = DUMMY_Y_GID

move_dummy_x = Move(target_id = DUMMY_X_GID, x = 1)
move_dummy_y = Move(target_id = DUMMY_Y_GID, y = 1)

move_dummy_x.group_id = INIT_SEQS_GID
move_dummy_y.group_id = INIT_SEQS_GID

move_dummy_x.spawn_trigger = True
move_dummy_x.multi_trigger = True
move_dummy_y.spawn_trigger = True
move_dummy_y.multi_trigger = True

sequences[0].add_target(END_GID) # ends the level

serialize = []
serialize = objects + sequence_spawners + sequences + extra_spawns + inv_scale_trigs + spawn_inv_scale_trigs + extra_inv_scale_trigs
serialize += list(move_x_trigs.values()) + list(move_y_trigs.values()) + list(scale_trigs.values())
serialize += [
    loop1, loop2, dummy_x, dummy_y, move_dummy_x, move_dummy_y, reset_move, inv_color_seq
]

obj_str = ''.join([str(obj) for obj in serialize])

with open("product/bad apple.gmd", 'w') as f:
    f.write(gmdify(obj_str))

print("Integers:", Sequence.nums)
print("Group ID's:", group_id_counter)