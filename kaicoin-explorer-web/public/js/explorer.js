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
            $('.three-balls').show();
            diagAlert.querySelector('.mdl-dialog__content').innerHTML = msg;
            diagAlert.showModal();
        };
        const diagTextAlert = document.querySelector('#diag-text-alert');
        if (!diagTextAlert.showModal) {
            dialogPolyfill.registerDialog(diagTextAlert);
        }
        diagTextAlert.querySelector('.close').addEventListener('click', function() {
            diagTextAlert.close();
        });
        // refer this https://stackoverflow.com/questions/1729501/javascript-overriding-alert?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
        window.textAlert = function(title, msg) {
            diagTextAlert.querySelector('.mtd-diag-title').innerHTML = title;
            diagTextAlert.querySelector('.mtd-diag-content-area').innerHTML = msg;
            diagTextAlert.showModal();
        };

        if (document.getElementById('search-keyword')!==null) {
            document.getElementById('search-keyword').onkeydown = function(e){
                if(e.keyCode===13){ self.beforeSearch(this.value); }
            };
        }
        $("#pagenation-blocks").mouseup(function() {
            self.paginateBlocks();
        });
        $("#pagenation-txs").mouseup(function() {
            const q = $(".thumb > .value").html();
            $("#progress-loader").addClass("is-active");
            $.getJSON('/txs/' + q, function(data) {
                console.log('txnum ' + q);
                $("#progress-loader").removeClass("is-active");
                $("#current-position > div").html('<i class="fas fa-arrow-down"></i>&nbsp;' + data.q);
                $("#mtd-txs-table > tbody").empty().html(self.makeTxsRow(data.list));
                window.location.href = '#' + q;
            });
        });
        console.log('path ' + window.location.pathname + ' ' + location.hash);
        // when 'block height' hash URL exists
        const pathname = window.location.pathname;
        if (pathname==='/blocks' && location.hash.startsWith("#")){
            console.log('go to paginate');
            $(".thumb > .value").html(location.hash.substring(1, location.hash.length));
            self.paginateBlocks();
        }
        if (pathname.startsWith("/summary")) {
            $(".mdl-navigation__link.btn-summary").addClass("on");
        } else if (pathname.startsWith("/block")) {
            $(".mdl-navigation__link.btn-blocks").addClass("on");
        } else if (pathname.startsWith("/tx")) {
            $(".mdl-navigation__link.btn-txs").addClass("on");
        }

    },
    showQRPopup: function(title, qrString) {
        alert('<div class=mtd-work-break>'+title+'</div><img class=mtd-diag-content-img src=https://api.qrserver.com/v1/create-qr-code/?size=208x208&data='+qrString+' onload=app.hidePopupLoader()>');
    },
    showQRText: function(title, text) {
        textAlert(title, text);
    },
    hidePopupLoader: function() {
        $('.three-balls').hide();
    },
    paginateBlocks: function() {
        const self = this;
        const q = $(".thumb > .value").html();
        $("#progress-loader").addClass("is-active");
        $.getJSON('/blocks/' + q, function(data) {
            console.log('blockheight ' + q);
            $("#progress-loader").removeClass("is-active");
            $("#current-position > div").html('<i class="fas fa-arrow-down"></i>&nbsp;' + data.q);
            $("#mtd-blocks-table > tbody").empty().html(self.makeBlocksRow(data.list));
            window.location.href = '#' + q;
        });
    },
    makeTxsRow: function(data) {
        const self = this;
        let rows = '';
        for (let i=0; i<data.length; i++) {

            const from = (data[i].txtype==='send' && typeof(data[i].vout[1])!=='undefined')
                ?'<div>' + data[i].vout[1].scriptPubKey.addresses[0] + '</div>':'';

            const to = ((data[i].txtype==='send' || data[i].txtype==='mine') && typeof(data[i].vout[0])!=='undefined')
                ?'<div><i class="fas fa-arrow-right"></i>&nbsp;' + data[i].vout[0].scriptPubKey.addresses[0] + '</div>':'';

            const amt = (typeof(data[i].vout)!=='undefined' && typeof(data[i].vout[0].value)!=='undefined')
                ?Number(data[i].vout[0].value).toLocaleString():'0';

            const labelSpanType = (typeof(data[i].ismemp)!=='undefined' && data[i].ismemp===true)?'<span class="label label-success">'
                :data[i].txtype==='mine'?'<span class="label">':data[i].txtype==='send'?'<span class="label label-primary">':'';

            console.log('data['+i+'] ' + labelSpanType);

            rows += '<tr><td>' + labelSpanType + data[i].txtype + '</span></td>'
                + '<td class="mdl-data-table__cell--non-numeric">' + '<a class="mtd-middle-chars" href="/tx/'+data[i].txid+'">'
                    + data[i].txid + '</a></td>'
                + '<td class="mdl-data-table__cell--non-numeric">' + from + to + '</td>'
                + '<td class="mtd-text-right">' + amt + ' KAI</td>'
                + '<td class="center"><span class="label">' + data[i].confirmations + '</span></td>'
                + '<td class="left"><i class="fas fa-arrow-down"></i>&nbsp;' + data[i].date + '</td></tr>';
        }
        console.log('data[0] ' + JSON.stringify(data[0]));
        return rows;
    },
    makeBlocksRow: function(data) {
        const self = this;
        let rows = '';
        for (let i=0; i<data.length; i++) {
            console.log('data['+i+'] ' + data[i].height);
            let txCount = '';
            if (data[i].txcount>1) {
                txCount = '<span class="label label-info">'+data[i].txcount+'</span>';
            } else {
                txCount = '<span class="label">'+data[i].txcount+'</span>';
            }
            rows += '<tr><td><a class="mtd-middle-chars mtd-label" href="/block/'+data[i].height+'">' +
                '<span class="label">'+data[i].height+'</span></a></td>' +
                '<td class="mdl-data-table__cell--non-numeric"><a class="mtd-middle-chars" href="/block/'+data[i].height+'">'+data[i].hash+'</a></td>' +
                '<td class="mdl-data-table__cell--non-numeric">'+data[i].miner+'</td>' +
                '<td>'+Number(data[i].size).toLocaleString()+'</td>' +
                '<td class="center">'+txCount+'</td>' +
                '<td class="center"><span class="label">'+data[i].confirmations+'</span></td>' +
                '<td class="left"><i class="fas fa-arrow-down"></i>&nbsp;'+data[i].date+'</td></tr>';
        }
        console.log('data[0] ' + JSON.stringify(data[0]));
        return rows;
    },
    beforeSearch: function(q) {
        const self = this;
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
