

/**
 * 时间格式化
 * @param x 时间。如new Date()
 * @param y 格式：如："yyyy-MM-dd hh:mm:ss"
 * @returns 格式化后的时间字符串
 */
function date2str(x,y) {
    var z = {M:x.getMonth()+1,d:x.getDate(),h:x.getHours(),m:x.getMinutes(),s:x.getSeconds()};
    y = y.replace(/(M+|d+|h+|m+|s+)/g,function(v) {return ((v.length>1?"0":"")+eval('z.'+v.slice(-1))).slice(-2)});
    return y.replace(/(y+)/g,function(v) {return x.getFullYear().toString().slice(-v.length)});
    }
function show_msg(msg, code){
	toastr.remove();
	if(code == 2){
		type = 'success';
	}else if(code == 4){
		type = 'error';
	}
	toastr[type]('<br>'+msg,'提示',{
        timeOut:1000,
        preventDuplicates:true,
    });
}
function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }