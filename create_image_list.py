import os

prefix = "/kaggle/input/20191027/27"

with open("eval_list.txt", "w") as f:
    files = sorted(os.listdir("F:/LSCDATA/keyframes/201910/27"))
    for file in files:
        f.write(f"{prefix}/{file}\n")