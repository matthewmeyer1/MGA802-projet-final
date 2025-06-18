from .aircraft import Aircraft
def write_planes(plane_list):
    for i in range(len(plane_list)):
        print(f"{i}    {plane_list[i].tail_num}")

def save_plane(plane_index, plane_list, folder_name):
    tail_num = plane_list[plane_index].tail_num

    with open(f"{folder_name}/{tail_num}.csv", "w") as f:
        for v in vars(plane_list[plane_index]).items():
            f.write(str(v[1]) + ",")

def load_plane(tail_num, plane_list, folder_name):
    with open(f"{folder_name}/{tail_num}.csv", "r") as f:
        line = f.readline()
        data = line.split(",")[:-1]

        return Aircraft(data[0], data[1], float(data[2]), float(data[3]), data[4], float(data[5]), float(data[6]), float(data[7]), float(data[8]))

