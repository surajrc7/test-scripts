#!/bin/bash
cd frontend 
npm start &
P2=$! 
cd ..
python project/manage.py runserver 0.0.0.0:8080  &
P1=$!
wait $P1 $P2
