"use strict";

$(function() {
    $("#uname").blur(function(){
        var uname = $(this).val();

        // 用户名格式校验
        if (uname.trim() === "") {
            $("#uname_tips").css("color", "red");
            $("#uname_tips").text("用户名不能为空！");
            return;
        }

        if (/[\u4E00-\u9FFF]/.test(uname)) {
            $("#uname_tips").css("color", "red");
            $("#uname_tips").text("用户名不能含有中文汉字！");
            return;            
        }

        if (uname.length < 4 || uname.length > 20) {
            $("#uname_tips").css("color", "red");
            $("#uname_tips").text("用户名至少为4个字符，最多为20个字符！");
            return;               
        }

        if (! /^[a-zA-Z0-9_]+$/.test(uname)) {
            $("#uname_tips").css("color", "red");
            $("#uname_tips").text("用户名只能包含字母、数字和下划线！");
            return;               
        }

        // 通过Ajax技术连接服务器后端校验用户名是否已被注册
        $.ajax({
            url: "/check_uname",
            data: {
                uname: uname
            },
            success: function(data){
                if (data["err"] === 0) {
                    // 用户名没有被注册
                    $("#uname_tips").css("color", "green");
                    $("#uname_tips").css("font-weight", "bold");
                    $("#uname_tips").text("√");
                } else if (data["err"] === 1) {
                    // 用户名已被注册
                    $("#uname_tips").css("color", "red");
                    $("#uname_tips").text("用户名已被注册！");
                }
            }
        });
    });

    $("#send_sms_code").click(function() {
        // 校验手机号格式
        var phone = $("#phone").val();

        if (! /1\d{10}/.test(phone)) {
            alert("手机号格式错误！");
            $("#phone").focus();
            return;
        }

        // 通过Ajax将手机号发送给服务器后端程序
        $.ajax({
            url: "/send_sms_code",
            data: {
                phone: phone
            },
            success: function(data){
                if (data["err"] === 0) {
                    // 成功
                    var s = 60;
                    $("#send_sms_code").prop("disabled", true);
                    $("#send_sms_code").html(s + "S");
                    
                    var timer = window.setInterval(function() {
                        --s;
                        if (s === 0) {
                            window.clearInterval(timer);
                            $("#send_sms_code").html("重新发送");
                            $("#send_sms_code").prop("disabled", false);
                            return;
                        }
            
                        $("#send_sms_code").html(s + "S");
                    }, 1000);                    
                } else {
                    // 失败
                    alert("发送短信验证码失败，" + data["desc"]);
                }
            },
            error: function(){
                alert("发送请求失败，请检查网络连接！");
            }
        });
    });
});