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
            $(".mtd-middle-top-wrapper").scrollLeft(-200);
            $("#im-scroll-right").show();
            $(this).hide();
        });
        console.log('path ' + window.location.pathname + ' ' + location.hash);
        // when 'block height' hash URL exists
        const pathname = window.location.pathname;
        if (pathname.startsWith("/summary")) {
            $(".mdl-navigation__link.btn-summary").addClass("on");
        } else if (pathname==='/blocks' && location.hash.startsWith("#")){
            console.log('go to paginate');
            $(".thumb > .value").html(location.hash.substring(1, location.hash.length));
            self.paginateBlocks();
        } else if (pathname==='/txs' && location.hash.startsWith("#")){
            console.log('go to paginate');
            $(".thumb > .value").html(location.hash.substring(1, location.hash.length));
            self.paginateTxs();
        } else if (pathname.startsWith("/block")) {
            $(".mdl-navigation__link.btn-blocks").addClass("on");
        } else if (pathname.startsWith("/tx")) {
            $(".mdl-navigation__link.btn-txs").addClass("on");
        }
        self.initSocket();

    },
    initSocket: function() {
        const self = this;
        let socket = io.connect();
        socket.on("message",     function(data) { self.onMessage('message', data)});
        socket.on("summary",     function(data) { self.onMessage('summary', data)});
        socket.on("recentblock", function(data) { self.onMessage('recentblock', data)});
        socket.on("recenttx",    function(data) { self.onMessage('recenttx', data)});
    },
    onMessage: function(type, data) {
        const self = this;
        if (type==='summary') {
            console.log('[message]' + type + ' ' + JSON.stringify(data));
        } else if (type==='recenttx') {
            const row = self.makeMainTxRow(data);
            // console.log('[message]' + type + ' ' + row);
            $("#latest-transactions").prepend(row);
            $("#latest-transactions tr:last-child").remove();
        } else if (type==='recentblock') {
            const row = self.makeMainBlockRow(data);
            // console.log('[message]' + type + ' ' + row);
            $("#latest-blocks").prepend(row);
            $("#latest-blocks tr:last-child").remove();
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
            $("#current-position > div").html('<i class="fas fa-arrow-up"></i>&nbsp;' + data.q);
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
            $("#current-position > div").html('<i class="fas fa-arrow-up"></i>&nbsp;' + data.q);
            $("#mtd-txs-table > tbody").empty().html(self.makeTxRows(data.list));
            window.location.href = '#' + q;
        });
    },
    makeTxRows: function(data) {
        const self = this;
        let rows = '';
        for (let i=0; i<data.length; i++) {
            rows += self.makeTxRow(data[i]);
         }
        console.log('data[0] ' + JSON.stringify(data[0]));
        return rows;
    },
    makeTxRow: function(datum) {
        const labelSpanType = datum.txtype==='mine'?'<span class="label">'
            :datum.txtype==='send'?'<span class="label label-primary">':'<span class="label label-success">';
        const from = datum.from.length<1?'':'<div>' + datum.from + '</div>';
        return '<tr><td class="mtd-td-label center">' + datum.seq + '</td><td class="mtd-td-label center">' + labelSpanType + datum.txtype + '</span></td>'
            + '<td class="mdl-data-table__cell--non-numeric hash mtd-work-break-ellipsis">' + '<a href="/tx/'+datum.txid+'">'
            + datum.txid + '</a></td>'
            + '<td class="mdl-data-table__cell--non-numeric hash mtd-work-break-ellipsis hide-under-small">'
            + from + '<div><i class="fas fa-arrow-right"></i>&nbsp;' + datum.to + '</div></td>'
            + '<td class="mtd-text-right">' + datum.amount + ' KAI</td>'
            + '<td class="center"><span class="label">' + datum.confirmations + '</span></td>'
            + '<td class="center"><i class="fas fa-arrow-up"></i>&nbsp;' + datum.date + '</td></tr>';
    },
    makeMainTxRow: function(datum) {
        const labelSpanType = datum.txtype==='mine'?'<span class="label">'
            :datum.txtype==='send'?'<span class="label label-primary">':'<span class="label label-success">';
        return '<tr><td class="center">' + labelSpanType + datum.txtype + '</span></td>'
            + '<td class="left-align mtd-txs-cell-tx hash mtd-work-break-middle-ellipsis">' + '<a href="/tx/'+datum.txid+'">'
            + datum.txid + '</a><br>'
            + '<div class="mtd-small-chars hide-under-small" style="line-height: 16px;overflow-x: hidden;">'
            + datum.from + '<i class="fas fa-arrow-right"></i>' + datum.to + '</div>'
            + '<td class="mtd-text-right" style="overflow-x: hidden; text-overflow: clip">' + datum.amount + '<span class="hide-under-small"> KAI</span></td>'
            + '<td class="center confirm"><span class="label">' + datum.confirmations + '</span></td>'
            + '<td class="left"><i class="fas fa-arrow-up"></i>' + datum.date + '</td></tr>';

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
                + data[i].confirmations+'</span></td><td class="center"><i class="fas fa-arrow-up"></i>&nbsp;'
                + data[i].date+'</td></tr>';
        }

        console.log('data[0] ' + JSON.stringify(data[0]));
        return rows;
    },
    makeMainBlockRow: function(datum) {
        const label = datum.txcount>1?'<span class="label label-info">':'<span class="label">';
        return '<tr><td class="center"><span class="label">' + datum.height + '</span></td>'
            + '<td class="left-align hash mtd-work-break-ellipsis"><a href="/block/'
            + datum.height + '">' + datum.hash + '</a></td><td class="center">'
            + label + datum.txcount + '</span></td><td class="center confirm"><span class="label">'
            + datum.confirmations + '</span></td><td>'
            + datum.size + '</td><td class="left"><i class="fas fa-arrow-up"></i>'
            + datum.date + '</td></tr>';
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
