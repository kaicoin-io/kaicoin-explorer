var app = {
    init: function() {
        const self = this;
        const diagAlert = document.querySelector('#diag-common-alert');
        if (!diagAlert.showModal) {
            dialogPolyfill.registerDialog(diagAlert);
        }
        diagAlert.querySelector('.close').addEventListener('click', function() {
            diagAlert.close();
        });
        // refer this https://stackoverflow.com/questions/1729501/javascript-overriding-alert?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
        window.alert = function(msg) {
            diagAlert.querySelector('.mdl-dialog__content').innerHTML = msg;
            diagAlert.showModal();
        };
        if (document.getElementById('search-keyword')!==null) {
            document.getElementById('search-keyword').onkeydown = function(e){
                if(e.keyCode == 13){ self.beforeSearch(this.value);}
            };
        }
    },
    beforeSearch: function(q) {
        console.log('beforeSearch keyword ' + q);
        $.getJSON('/q/' + q, function(data) {
            console.log('data ' + JSON.stringify(data));
            if (data.type!==null) {
                window.location.href = '/' + data.type + '/' + q;
            }
        });
    }
};
/*
const socket = io('/'); // '/'
socket.on('connect', function () {
    console.log('io connected');
});
socket.on('connection', function (data) {
    console.log('io connection');
});
socket.on('message', function (data) {
    console.log('io message ' + JSON.stringify(data));
    // socket.emit('message', {'name': 'client'});
});
*/
