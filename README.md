# kaicoin-explorer
Blockchain explorer of Kaicoin

I. Ingredients

  1. Node.JS - base web framework:
    - https://nodejs.org/
  2. Fastify - faster web: 
    - https://www.fastify.io/
    - https://www.npmjs.com/package/fastify
  3. RethinkDB - for Realtime NoSQL database: 
    - https://www.rethinkdb.com/
    - https://www.npmjs.com/package/rethinkdb
  4. node-schedule - to syncronize data with the blockchain blocks: 
    - https://github.com/node-schedule/node-schedule
    - https://www.npmjs.com/package/node-schedule
  5. Socket.io - to apply realtime data changes to UI:
    - https://socket.io/
    - https://www.npmjs.com/package/socket.io
  6. Multichain API - easy to explore blockchain on Node.JS environment
    - https://tilkal.github.io/multichain-api/
    - https://www.npmjs.com/package/multichain-api

II. Installation on Ubuntu (v16 recommended)

  1. Package update
    - sudo apt-get update
  2. Nginx install
    - sudo apt-get -y install nginx
  3. Nodejs install
    - sudo apt-get -y install nodejs
  4. Rethink DB install (refer to this: https://rethinkdb.com/docs/install/ubuntu/)
    - source /etc/lsb-release && echo "deb http://download.rethinkdb.com/apt $DISTRIB_CODENAME main" | sudo tee /etc/apt/sources.list.d/rethinkdb.list
    - sudo apt-get -y install rethinkdb 
    - wget -qO- https://download.rethinkdb.com/apt/pubkey.gpg | sudo apt-key add -
    - sudo apt-get update
    - sudo apt-get install rethinkdb
  5. Multichain install (refer to this: https://www.multichain.com/download-install/)
    - wget https://www.multichain.com/download/multichain-1.0.4.tar.gz
    - tar -xvzf multichain-1.0.4.tar.gz
    - cd multichain-1.0.4
    - mv multichaind multichain-cli multichain-util /usr/local/bin (to make easily accessible on the command line)
  6. Upload files via SFTP/FTP
