var app = {
    init: function() {
        if (document.getElementById('search-keyword')!==null) {
            document.getElementById('search-keyword').onkeydown = function(e){
                if(e.keyCode == 13){
                    // submit
                    console.log('onSearch');
                }
            };
        }
    },
    // onSearch: function(form) {
    //     console.log('onSearch');
    //     if(form.keyCode==13){
    //         alert('search');
    //         // form.submit();
    //     }
    // }
};