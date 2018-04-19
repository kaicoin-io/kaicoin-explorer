var app = {
    init: function() {
        document.getElementById('search-keyword').onkeydown = function(e){
            if(e.keyCode == 13){
                console.log('onSearch');
                // submit
            }
        };
    },
    // onSearch: function(form) {
    //     console.log('onSearch');
    //     if(form.keyCode==13){
    //         alert('search');
    //         // form.submit();
    //     }
    // }
};