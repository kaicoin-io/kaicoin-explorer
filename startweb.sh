cd web
sudo forever start -o ../web.log -e ../err-web.log start ./web.js
# sudo nohup node ./web.js &> ../web.log&