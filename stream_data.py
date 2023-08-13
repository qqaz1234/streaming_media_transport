#!/usr/bin/env python
# -*- coding=utf-8 -*-
import datetime
import numpy as np
import cv2 as cv
import threading
import time
import select
import cryptocode
#!/usr/bin/env python
import numpy as np
import cv2#opencv包
import os
from os import mkdir
from os.path import isdir
import datetime
import psycopg2#数据库包
import pyaudio
import socket
import sys
from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT
import base64
import wave

print('this is Server')

#加密密钥
key = b'1111111111111111'
iv = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' #  bytes类型
crypt_sm4 = CryptSM4()
#设置摄像头显示画面的大小
cap = cv.VideoCapture(0)  # 调取内部摄像头
ret, frame = cap.read()  # 读取视频帧
#音频格式
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 4096
#调用windows内部声卡
audio = pyaudio.PyAudio()
#创建声音的socket通信
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
read_list = [serversocket]
#创建视频文件
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#设置日期
now = str(datetime.datetime.now())[:19].replace(':', '_')
dirName = now[:10]      #目录名
video_tempAviFile = dirName+'//'+now+'.avi'       #视频文件名
audio_tempWavFile = dirName+'//'+'wav'+'//'+now+'.wav'
if not isdir(dirName):      #创建目录
    mkdir(dirName)
out = cv2.VideoWriter(video_tempAviFile, fourcc, 1, (640,480))
#调出文件夹中文件数
video_path = 'C:/Users/jihongxin/PycharmProjects/pythonProject/test/'+dirName     # 输入文件夹地址
video_files = os.listdir(video_path)     # 读入文件夹
num_video = len(video_files)       # 统计文件夹中的文件个数
#调用文件夹的音频文件数
audio_path = "C://Users//jihongxin//PycharmProjects//pythonProject//test//"+dirName+'//'+'wav'  # 输入文件夹地址
audio_files = os.listdir(audio_path)     # 读入文件夹
num_audio = len(audio_files)       # 统计文件夹中的文件个数
#shujuku
conn = psycopg2.connect(dbname="postgres",
                        user="dboper",
                        password="dboper@123",
                        host="192.168.114.129",
                        port="26000")
conn.set_client_encoding('utf8')
cur = conn.cursor()

#视频服务端
def Videoserver():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#标明IPV4以及采用协议
        s.bind(('127.0.0.1', 6666))#绑定端口以及ip地址
        s.listen(15)#监听
    except:
        sys.exit(1)
    print('Waiting connection...')
    while True:
        conn, addr = s.accept()#接收描述字和指针
        t = threading.Thread(target=deal_data, args=(conn, addr))#创建线程增加图片传输速率
        t.start()#开始线程



#处理图像数据
def deal_data(conn, addr):
    print('Accept new connection from {0}'.format(addr))
    while True:
        # get a frame
        ret,frame = cap.read()#读取视频帧
        #加水印
        # font = cv.FONT_HERSHEY_SIMPLEX
        # datet = str(datetime.datetime.now())
        # text1 = '2020213373  ji hong xin'
        # frame_watermark = cv.putText(frame, datet, (10, 100), font, 1,(0, 255, 255), 2, cv.LINE_AA)
        # frame_watermark = cv.putText(frame, text1, (10, 150), font, 0.9,(255, 0, 0), 2, cv.LINE_AA)
        # enimage=encode(frame)#加密加过水印后的图像
        #进行传输编码
        img = cv.imencode('.jpg', frame)[1]
        data_encode = np.array(img)
        str_encode = data_encode.tostring()
        # imgstr_encode=base64.b64encode(str_encode)
        # crypt_sm4.set_key(key, SM4_ENCRYPT)
        # imgstr_encode = crypt_sm4.crypt_ecb(str_encode)  # bytes类型
        # print(imgstr_encode)
        try:
            conn.send(str_encode)  # 发送图片的encode码
        except:
            print('wait')
        time.sleep(0.4)
    conn.close()


def callback(in_data, frame_count, time_info, status):
    for s in read_list[1:]:
        # encode_data=base64.b64encode(in_data)
        s.send(in_data)

    return (in_data, pyaudio.paContinue)


def audioserver():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 标明IPV4以及采用协议
    serversocket.bind(('127.0.0.1', 4444))
    serversocket.listen(5)
    # start Recording
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK,stream_callback=callback)
    # stream.start_stream()

    print("recording...")

    try:
        while True:
            readable, writable, errored = select.select(read_list, [], [])
            for s in readable:
                if s is serversocket:
                    (clientsocket, address) = serversocket.accept()
                    read_list.append(clientsocket)
                    print("Connection from"), address
                else:
                    data = s.recv(1024)
                    if not data:
                        read_list.remove(s)
    except KeyboardInterrupt:
        pass
    print('finished recording')
    serversocket.close()
    # 停止记录，关闭声卡
    stream.stop_stream()
    stream.close()
    audio.terminate()


#数据库函数
def database():
    conn = psycopg2.connect(dbname="postgres",
                            user="dboper",
                            password="dboper@123",
                            host="192.168.114.129",
                            port="26000")
    conn.set_client_encoding('utf8')
    cur = conn.cursor()
    cur.execute(
        '''
        CREATE TABLE video(
            num_video INT PRIMARY KEY     NOT NULL,
            video_tempaAviFile          CHAR(50),
            audio_tempaAviFile          CHAR(50)
            )
        ''')
    # 数据插入
    cur.execute("INSERT INTO Video(ID,PATH) \
          VALUES ('%s', '%s','%s')"%(num_video,video_tempAviFile,audio_tempWavFile));
    conn.commit()

    # 数据查询
    cur.execute("SELECT id,path  from Video")
    rows = cur.fetchall()
    for row in rows:
        print("ID = ", row[0])
        print("PATH = ", row[1])
    conn.close()


#视频客户端设置
def videoclient():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', 6666))  # 连接服务端
        cur.execute("INSERT INTO video(num_video,video_tempaaviFile) \
                  VALUES ('%s', '%s')" % (num_video, video_tempAviFile));
        conn.commit()
    except socket.error as msg:
        print(msg)
        sys.exit(1)
    # c_sock, c_addr =s.accept()
    print('this is Client')
    while True:
        try:
            receive_encode = s.recv(777777)  # 接收的字节数 最大值 2147483647 （31位的二进制）
            # crypt_sm4.set_key(key, SM4_DECRYPT)
            # imgstr_decode = crypt_sm4.crypt_ecb(receive_encode)  # bytes类型
            # base64_imgstr_decode = base64.b64decode(imgstr_decode)qqq
            nparr_decode = np.fromstring(receive_encode, np.uint8)
            img_decode = cv2.imdecode(nparr_decode, cv2.IMREAD_COLOR)#图片解码
            out.write(img_decode)  # 写入视频帧
            cv2.imshow("jie mi",img_decode)

            #当按下键盘esc时，退出录制
            if cv2.waitKey(1)==27:
               break
        except Exception as e:
            print(e)


wf = wave.open(audio_tempWavFile, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(audio.get_sample_size(FORMAT))
wf.setframerate(RATE)
cur.execute("INSERT INTO audio(num_audio,audio_tempaaviFile) \
                      VALUES ('%s', '%s')" % (num_audio, audio_tempWavFile));
conn.commit()
def audioclient():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 4444))
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
    try:
        while True:
            data = s.recv(CHUNK)
            # decode_data=base64.b64decode(data)
            stream.write(data)
            # frames = pickle.loads(decode_data)
            wf.writeframes(data)
            # if cv2.waitKey(1000) & 0xFF == ord('q'):
            #     break
    except KeyboardInterrupt:
        pass
    print('Shutting down')
    s.close()
    stream.close()
    audio.terminate()

#四个线程设置，让几个线程同时运行
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=4) as executor:
    executor.submit(videoclient)
    executor.submit(audioclient)
    executor.submit(Videoserver)
    executor.submit(audioserver)


Videoserver()
audioserver()
videoclient()
audioclient()
database()



