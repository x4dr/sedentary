function countdownIn(countDownDate, counter) {

    var x = setInterval(function () {

        var distance = countDownDate - new Date().getTime()/1000;
        var days = Math.floor(distance / (60 * 60 * 24));
        var hours = Math.floor((distance % (60 * 60 * 24)) / (60 * 60));
        var minutes = Math.floor((distance % (60 * 60)) / 60);
        var seconds = Math.floor(distance % 60);

        counter.innerHTML = "";
        if (days > 0) {
            counter.innerHTML += days + ":";
        }
        if (days > 0 || hours > 0) {
            counter.innerHTML += ("0"+hours).slice(-2) + ":";
        }
        counter.innerHTML += ("0"+minutes).slice(-2) + ":" + ("0"+seconds).slice(-2);

        // If the count down is over, write some text
        if (distance < 0) {
            clearInterval(x);
            counter.innerHTML = "DONE";
        }
    }, 1000);

}

