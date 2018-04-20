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
                if(e.keyCode===13){ self.beforeSearch(this.value); }
            };
        }
        $("#pagenation-blocks").mouseup(function() {
            const q = $(".thumb > .value").html();
            $("#progress-loader").addClass("is-active");
            $.getJSON('/blocks/' + q, function(data) {
                console.log('blockheight ' + q);
                $("#progress-loader").removeClass("is-active");
                $("#current-position").text(data.q);
                $("#mtd-blocks-table > tbody").empty().html(self.makeBlocksRow(data.list));
                window.location.href = '#' + q;
            });
        });
        $("#pagenation-txs").mouseup(function() {
            const q = $(".thumb > .value").html();
            $("#progress-loader").addClass("is-active");
            $.getJSON('/txs/' + q, function(data) {
                console.log('txnum ' + q);
                $("#progress-loader").removeClass("is-active");
                $("#current-position").text(data.q);
                $("#mtd-txs-table > tbody").empty().html(self.makeTxsRow(data.list));
                window.location.href = '#' + q;
            });
        });
    },
    makeTxsRow: function(data) {
        let rows = '';
        for (let i=0; i<data.length; i++) {
            console.log('data['+i+'] ' + data[i].height);
            rows += '<tr><td><a class="mtd-middle-chars mtd-label" href="/block/'+data[i].height+'">' +
                '<span class="label label-info">'+data[i].height+'</span></a></td>' +
                '<td class="mdl-data-table__cell--non-numeric"><a class="mtd-middle-chars ellipse" href="/block/'+data[i].height+'">'+data[i].hash+'</a></td>' +
                '<td class="mdl-data-table__cell--non-numeric"><a class="mtd-middle-chars ellipse" href="#">'+data[i].miner+'</a></td>' +
                '<td>'+data[i].size+'</td><td><span class="label label-info">'+data[i].txcount+'</span></td><td class="center">' +
                '<span class="label label-info">'+data[i].confirmations+'</span></td>' +
                '<td><i class="fas fa-arrow-down"></i>&nbsp;'+data[i].date+'</td></tr>';
        }
        console.log('data[0] ' + JSON.stringify(data[0]));
        return rows;
    },
    makeBlocksRow: function(data) {
        let rows = '';
        for (let i=0; i<data.length; i++) {
            console.log('data['+i+'] ' + data[i].height);
            rows += '<tr><td><a class="mtd-middle-chars mtd-label" href="/block/'+data[i].height+'">' +
                '<span class="label label-info">'+data[i].height+'</span></a></td>' +
                '<td class="mdl-data-table__cell--non-numeric"><a class="mtd-middle-chars ellipse" href="/block/'+data[i].height+'">'+data[i].hash+'</a></td>' +
                '<td class="mdl-data-table__cell--non-numeric"><a class="mtd-middle-chars ellipse" href="#">'+data[i].miner+'</a></td>' +
                '<td>'+data[i].size+'</td><td><span class="label label-info">'+data[i].txcount+'</span></td><td class="center">' +
                '<span class="label label-info">'+data[i].confirmations+'</span></td>' +
                '<td><i class="fas fa-arrow-down"></i>&nbsp;'+data[i].date+'</td></tr>';
        }
        console.log('data[0] ' + JSON.stringify(data[0]));
        return rows;
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
