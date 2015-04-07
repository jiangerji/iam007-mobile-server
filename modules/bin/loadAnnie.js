var page = require('webpage').create();
var fs = require('fs');

var system = require('system');
var args = system.args;

// args.forEach(function(arg, i) {
//   console.log(i + ': ' + arg);
// });

var url = args[1]
var output = args[2]

page.settings.userAgent = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)';

page.onResourceRequested = function (request) {
    // console.log('Request ' + JSON.stringify(request, undefined, 4));
};
page.onResourceReceived = function (response) {
    // console.log('Receive ' + JSON.stringify(response, undefined, 4));
};

var t = Date.now();

var timeoutCount = 0;

function checkLoadComplete(){
    fs.write(output, page.content, "w");
    phantom.exit();
    // if (page.content.indexOf("商品介绍加载中...") < 0){
    //     fs.write(output, page.content, "w")
    //     t = Date.now() - t;
    //     console.log('loading finish time ' + t + ' msec');
    //     phantom.exit();
    // } else {
    //     timeoutCount++;
    //     if (timeoutCount > 50){
    //         phantom.exit();
    //     } else {
    //         setTimeout(checkLoadComplete, 200);
    //     }
    // }
}

page.open(url, function(status) {
    console.log("open Status: " + status);
    if(status === "success") {
        p = Date.now() - t;
        console.log('get webpage time ' + p + ' msec');
        setTimeout(checkLoadComplete, 10);
    } else {
        phantom.exit();
    }
});
