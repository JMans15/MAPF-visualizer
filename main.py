import PySimpleGUI as sg, numpy as np, os, subprocess

Map = None
Agents = None
width, height = 0, 0
Single = False
exec_name = './TFE_MAPF_visu'

canvas_column = [
    [
        sg.Canvas(size=(512, 512), background_color="white", key="canvas"),
    ]
]

single_paths = [
    [
        sg.Text("Source", size=(12, 1)),
        sg.Text("x: ", size=(1, 1)),
        sg.In(size=(9, 1), enable_events=True, key="single_sourcex"),
        sg.Text("y: ", size=(1, 1)),
        sg.In(size=(8, 1), enable_events=True, key="single_sourcey"),
    ],
    [
        sg.Text("Target", size=(12, 1)),
        sg.Text("x: ", size=(1, 1)),
        sg.In(size=(9, 1), enable_events=True, key="single_targetx"),
        sg.Text("y: ", size=(1, 1)),
        sg.In(size=(8, 1), enable_events=True, key="single_targety"),
        sg.Button("Submit", key='single_submit', enable_events=True, size=(6, 1)),
    ],
]

multi_paths = [
    [
        sg.Text("Scenario file", size=(12, 1)),
        sg.In(size=(25, 1), enable_events=True, key="scenfile"),
        sg.FolderBrowse(size=(6, 1)),
    ],
    [
        sg.Listbox(values=[], enable_events=True, size=(49, 20), key="scenlist"),
    ],
]

settings_column = [
    [
        sg.Column([[sg.Text("Settings")]])
    ],
    [
        sg.HSeparator()
    ],
    [
        sg.Column([[
        sg.Text("Map file", size=(12, 1)),
        sg.In(size=(25, 1), enable_events=True, key="mapfile"),
        sg.FileBrowse(size=(6, 1)),
        ]])
    ],
    [
        sg.HSeparator(),
    ],
    [
        sg.Column(multi_paths, key="multi_paths", visible=True),
        sg.Column(single_paths, key="single_paths", visible=False),
    ],
    [
        sg.HSeparator(),
    ],
    [
        sg.Button("Clear", key='clear', enable_events=True),
        sg.Button("Switch mode", key='switch', enable_events=True),
        sg.Button("Read res", key='res', enable_events=True),
        sg.Button("Play", key='play', enable_events=True),
        sg.Button("Solve", key='solve', enable_events=True),
    ]
]

layout = [
    [
        sg.Column(canvas_column),
        sg.VSeperator(),
        sg.Column(settings_column)
    ]
]

window = sg.Window("Visualizer", layout)

def draw_map():
    if Map is None:
        return
    canvas_w = window["canvas"].get_size()[0]
    canvas = window["canvas"].TKCanvas
    size = canvas_w / width
    for x in range(width):
        for y in range(height):
            if Map[y, x]:
                canvas.create_rectangle(x*size, y*size, x*size+size, y*size+size, fill="black", outline="black")

def parseMapFile(file_):
    global Map, width, height
    with open(file_, "r") as f:
        lines = f.readlines()

        Map = np.array(
            [
            list(map(lambda x: x!='.', list(l.strip())))
            for l in lines[4:]
            ], 
            dtype=bool)
        width, height = Map.shape

def draw_agents():
    if Agents is None:
        return
    canvas_w = window["canvas"].get_size()[0]
    canvas = window["canvas"].TKCanvas
    size = canvas_w / width
    for agent in Agents:
        canvas.create_rectangle(agent[0]*size, agent[1]*size, agent[0]*size+size, agent[1]*size+size, fill="red", outline="red")
        canvas.create_rectangle(agent[2]*size, agent[3]*size, agent[2]*size+size, agent[3]*size+size, fill="green", outline="green")

def draw_paths(paths):
    canvas_w = window["canvas"].get_size()[0]
    canvas = window["canvas"].TKCanvas
    size = canvas_w / width
    for path in paths:
        for i in range(1, len(path)):
            canvas.create_line(path[i-1, 0]*size+size/2, path[i-1, 1]*size+size/2, path[i, 0]*size+size/2, path[i, 1]*size+size/2, fill="blue", width=2)
    
def draw_agents_path(positions):
    canvas_w = window["canvas"].get_size()[0]
    canvas = window["canvas"].TKCanvas
    size = canvas_w / width
    for position in positions:
        canvas.create_rectangle(position[0]*size, position[1]*size, position[0]*size+size, position[1]*size+size, fill="red", outline="red")

def draw():
    canvas = window["canvas"].TKCanvas
    canvas.delete("all")
    draw_map()
    draw_agents()

def parseScenFile(filename):
    global Agents
    with open(filename, "r") as f:
        lines = f.readlines()
        Agents = np.empty((len(lines)-1, 4), dtype=int)
        for i, line in enumerate(lines[1:]):
            data = np.array(line.strip().split('\t')[4:8]).astype(int)
            Agents[i, :] = data


def parseResult(filename):
    with open(filename, "r") as f:
        lines = f.readlines()
        nagents, T = lines[0].strip().split(' ')
        nagents, T = int(nagents), int(T)
        paths = np.empty((nagents, T, 2), dtype=int)
        for i in range(T):
            for j in range(nagents):
                paths[j, i, :] = np.array(lines[i*nagents+j+1].strip().split(',')).astype(int)
        return paths


playing = False
step = 0
while True:
    event, values = window.read()
    if event == "Exit" or event == sg.WIN_CLOSED:
        break

    if event == "mapfile":
        parseMapFile(values["mapfile"])
        draw()
    
    elif event == "scenfile":
        folder = values["scenfile"]
        file_list = os.listdir(folder)
        fnames = [
            f
            for f in file_list
            if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith(".scen")
        ]
        window["scenlist"].update(fnames)

    elif event == "scenlist":
        if Map is None:
            sg.popup("Please select a map file first")
            continue
        filename = os.path.join(
            values["scenfile"], values["scenlist"][0]
        )
        parseScenFile(filename)
        draw()

    elif event == "clear":
        playing = False
        Map = None
        Agents = None
        height, width = 0, 0
        window["canvas"].TKCanvas.delete("all")
        window["scenlist"].update([])
        window["mapfile"].update("")
        window["scenfile"].update("")
        window["single_sourcex"].update("")
        window["single_sourcey"].update("")
        window["single_targetx"].update("")
        window["single_targety"].update("")

    elif event == "switch":
        Single = not Single
        window["single_paths"].update(visible=Single)
        window["multi_paths"].update(visible=not Single)
        if Single:
            window["scenlist"].update([])
            window["scenfile"].update("")
            Agents = None
        else:
            window["single_sourcex"].update("")
            window["single_sourcey"].update("")
            window["single_targetx"].update("")
            window["single_targety"].update("")
            Agents = None

    elif event == "single_submit":
        if Map is None:
            sg.popup("Please select a map file first")
            continue
        if Agents is None:
            Agents = np.zeros((1, 4), dtype=int)
        x = int(values["single_sourcex"])
        y = int(values["single_sourcey"])
        Agents[0, :2] = [x, y]
        x = int(values["single_targetx"])
        y = int(values["single_targety"])
        Agents[0, 2:] = [x, y]
        draw()

    elif event == "res":
        paths = parseResult("result.txt")
        draw_paths(paths)
    elif event == "play":
        paths = parseResult("result.txt")
        playing = True
        step = 0
    
    elif event == "solve":
        torun = [exec_name, \
            "--map", values['mapfile'], \
            "-a", f'10', \
            "--outfile", "./result.txt"]
        if not Single:
            torun.append('-m')
            torun.append('--scen')
            torun.append(os.path.join(values["scenfile"], values["scenlist"][0]))
        subprocess.run(torun)

    if playing:
        if step < paths.shape[1]:
            draw_agents_path(paths[:, step, :].reshape(-1, 2))
            step += 1
        else:
            playing = False
            step = 0


window.close()
