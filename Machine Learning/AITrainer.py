import cv2
import numpy as np
import time
import PoseModule as pm
import requests
import pygame
import streamlit as st

cap = cv2.VideoCapture(0)
detector = pm.PoseDetector()
pTime = 0
frame_placeholder = st.empty()

st.title("🏋️‍♂️ AI-Based Exercise Tracker")
st.sidebar.header("Exercise Selection")
exercise_type = st.sidebar.selectbox("Choose an Exercise", ["Bicep Curl", "Squat", "Push-up"])

pygame.mixer.init()
song = pygame.mixer.Sound("sound.mp3")

url = "http://localhost:3000/api/countinc"


if "start" not in st.session_state:
    st.session_state["start"] = False
if "stop" not in st.session_state:
    st.session_state["stop"] = False
if "count" not in st.session_state:
    st.session_state["count"] = 0
if "dir" not in st.session_state:
    st.session_state["dir"] = 0

if st.sidebar.button("Start Exercise",key=465):
    st.session_state["start"] = True
    st.session_state["stop"] = False

if st.sidebar.button("Stop Exercise",key=487):
    st.session_state["stop"] = True
    st.session_state["start"] = False

if st.session_state["start"] and not st.session_state["stop"]:
    while cap.isOpened():
        success, img = cap.read()
        if not success:
            st.error("Failed to capture video")
            break
        img = cv2.resize(img, (1280, 720))
        img = detector.findPose(img, False)
        lmList = detector.findPosition(img, False)

        if len(lmList) != 0:
            if detector.current_exercise == pm.ExerciseType.BICEP_CURL:
                angle_right = detector.findAngle(img, 12, 14, 16)  #Right arm
                angle_left = detector.findAngle(img, 11, 13, 15)   #Left arm
                angle = (angle_right + angle_left) / 2
                per_right = np.interp(angle_right, (30, 160), (0, 100))  
                per_left = np.interp(angle_left, (30, 160), (0, 100))    
                per = min(per_right, per_left)  

            elif detector.current_exercise == pm.ExerciseType.PUSHUP:
                angle_right = detector.findAngle(img, 12, 14, 16)  
                angle_left = detector.findAngle(img, 11, 13, 15) 
                angle = (angle_right + angle_left) / 2
                per_right = np.interp(angle_right, (30, 160), (0, 100))  
                per_left = np.interp(angle_left, (30, 160), (0, 100))    
                per = min(per_right, per_left)  

            elif detector.current_exercise == pm.ExerciseType.SQUAT:
                angle_right_leg = detector.findAngle(img, 24, 26, 28)  #Right leg
                angle_left_leg = detector.findAngle(img, 23, 25, 27)   #Left leg
                angle = (angle_right + angle_left) / 2
                per_right_leg = np.interp(angle_right_leg, (170, 90), (0, 100)) 
                per_left_leg = np.interp(angle_left_leg, (170, 90), (0, 100))    
                per = min(per_right_leg, per_left_leg)  

            per = np.interp(angle, (210, 310), (0, 100))
            bar = np.interp(angle, (220, 310), (650, 100))

            color = (255, 0, 255)
            if per == 100:
                color = (0, 255, 0)
                if st.session_state["dir"] == 0:
                    st.session_state["count"] += 0.5
                    st.session_state["dir"] = 1
                    try:
                        data = {"count": int(st.session_state["count"])}
                        response = requests.post(url, json=data)
                        print(response.status_code, response.text)
                    except requests.exceptions.RequestException as e:
                        print(f"Error sending request: {e}")

                    if st.session_state["count"] % 1 == 0: 
                        song.play()  
                        print("Exercise completed! Song is playing!")

            if per == 0:
                color = (0, 255, 0)
                if st.session_state["dir"]  == 1:
                    st.session_state["count"] += 0.5
                    st.session_state["dir"] = 0
                    try:
                        data = {"count": int(st.session_state["count"])}
                        response = requests.post(url, json=data)
                        print(response.status_code, response.text)
                    except requests.exceptions.RequestException as e:
                        print(f"Error sending request: {e}")

                    if st.session_state["count"] % 1 == 0: 
                        song.play()  
                        print("Exercise completed! Song is playing!")

            cv2.rectangle(img, (1100, 100), (1175, 650), color, 3)
            cv2.rectangle(img, (1100, int(bar)), (1175, 650), color, cv2.FILLED)
            cv2.putText(img, f'{int(per)} %', (1100, 75), cv2.FONT_HERSHEY_PLAIN, 4,
                        color, 4)

            cv2.rectangle(img, (0, 450), (250, 720), (0, 255, 0), cv2.FILLED)
            cv2.putText(img, str(int(st.session_state["count"])), (45, 670), cv2.FONT_HERSHEY_PLAIN, 15,
                        (255, 0, 0), 25)
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, str(int(fps)), (50, 100), cv2.FONT_HERSHEY_PLAIN, 5,
                    (255, 0, 0), 5)

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        st.markdown("""
                    <style>
                    img {
                        max-width: 100%;
                        height: auto;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
        frame_placeholder.image(img, channels="RGB", use_container_width=True)
        
        if st.session_state["stop"]:
            st.warning("Exercise tracking stopped.")
            break