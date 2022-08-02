#!/bin/bash
cd /app/frontend 
npm start &
P2=$! 
python /app/project/manage.py runserver 0.0.0.0:8080  &
P1=$!
wait $P1 $P2