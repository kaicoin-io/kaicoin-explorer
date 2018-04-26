'use strict';

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
        $("#mtd-btn-search").click(function(){
            self.beforeSearch($("#search-keyword").val());
        });
        $("#pagenation-blocks").mouseup(function() {
            self.paginateBlocks();
        });
        $("#pagenation-blocks").bind("touchend", function() {
            self.paginateBlocks();
        });
        $("#pagenation-txs").mouseup(function() {
            self.paginateTxs();
        });
        $("#pagenation-txs").bind("touchend", function(e) {
            self.paginateTxs();
        });
        $("#im-scroll-right").click(function() {
            $(".mtd-middle-top-wrapper").scrollLeft(200);
            $("#im-scroll-left").show();
            $(this).hide();
        });
        $("#im-scroll-left").click(function() {
            console.log("clicked");
            $(".mtd-middle-top-wrapper").scrollLeft(-200);
            $("#im-scroll-right").show();
            $(this).hide();
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
            $("#mtd-blocks-table > tbody").empty().html(self.makeBlockRow(data.list));
            window.location.href = '#' + q;
        });
    },
    paginateTxs: function() {
        const self = this;
        const q = $(".thumb > .value").html();
        $("#progress-loader").addClass("is-active");
        $.getJSON('/txs/' + q, function(data) {
            console.log('tx idx ' + q);
            $("#progress-loader").removeClass("is-active");
            $("#current-position > div").html('<i class="fas fa-arrow-down"></i>&nbsp;' + data.q);
            $("#mtd-txs-table > tbody").empty().html(self.makeTxRow(data.list));
            window.location.href = '#' + q;
        });
    },
    makeTxRow: function(data) {
        const self = this;
        let rows = '';
        for (let i=0; i<data.length; i++) {

            // const from = (data[i].txtype==='send' && data[i].vout[1])
            //     ?'<div>' + data[i].vout[1].scriptPubKey.addresses[0] + '</div>':'';
            // const to = ((data[i].txtype==='send' || data[i].txtype==='mine') && data[i].vout && data[i].vout[0])
            //     ?'<div><i class="fas fa-arrow-right"></i>&nbsp;' + data[i].vout[0].scriptPubKey.addresses[0] + '</div>':'';
            const labelSpanType = data[i].txtype==='mine'?'<span class="label">'
                :data[i].txtype==='send'?'<span class="label label-primary">':'<span class="label label-success">';
            const from = data[i].from.length<1?'':'<div>' + data[i].from + '</div>';
            rows += '<tr><td class="mtd-td-label center">' + labelSpanType + data[i].txtype + '</span></td>'
                + '<td class="mdl-data-table__cell--non-numeric hash mtd-work-break-ellipsis">' + '<a href="/tx/'+data[i].txid+'">'
                + data[i].txid + '</a></td>'
                + '<td class="mdl-data-table__cell--non-numeric hash mtd-work-break-ellipsis hide-under-small">'
                + from + '<div><i class="fas fa-arrow-right"></i>&nbsp;' + data[i].to + '</div></td>'
                + '<td class="mtd-text-right">' + data[i].amount + ' KAI</td>'
                + '<td class="center"><span class="label">' + data[i].confirmations + '</span></td>'
                + '<td class="center"><i class="fas fa-arrow-down"></i>&nbsp;' + data[i].date + '</td></tr>';
        }
        console.log('data[0] ' + JSON.stringify(data[0]));
        return rows;
    },
    makeBlockRow: function(data) {
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
            rows += '<tr><td class="center"><span class="label">'
                + data[i].height+'</span></td>'
                + '<td class="mdl-data-table__cell--non-numeric hash mtd-work-break-ellipsis"><a href="/block/'
                + data[i].height+'">'+data[i].hash+'</a></td>'
                + '<td class="mdl-data-table__cell--non-numeric hash mtd-work-break-ellipsis hide-under-small">'
                + data[i].miner+'</td><td>'
                + Number(data[i].size).toLocaleString() + '</td><td class="center">'
                + txCount + '</td><td class="center"><span class="label">'
                + data[i].confirmations+'</span></td><td class="center"><i class="fas fa-arrow-down"></i>&nbsp;'
                + data[i].date+'</td></tr>';
        }

        console.log('data[0] ' + JSON.stringify(data[0]));
        return rows;
    },
    beforeSearch: function(q) {
        if (q.length<1) return;
        const self = this;
        console.log('beforeSearch keyword ' + q);
        $.getJSON('/q/' + q, function(data) {
            console.log('data ' + JSON.stringify(data));
            if (data.type!==null && data.type!=='none') {
                window.location.href = '/' + data.type + '/' + q;
            } else {
                var snackbarContainer = document.querySelector('#mtd-snack-empty-search');
                const data = {message: 'NO SEARCH RESULT'};
                snackbarContainer.MaterialSnackbar.showSnackbar(data);
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
