function sendMessage() {
    const messageInput = document.getElementById("messageinput").value;
    console.log(messageInput)
    document.getElementById("messageinput").value = null;
}
function shownewchatmenu() {
    if (document.getElementById("newchatmenu").style.display!="flex") {
        document.getElementById("newchatmenu").style.display="flex";
        document.getElementById("newchatmenu").focus();
        document.getElementById("container2").style.filter = "blur(5px)";
    }
}
window.onload = function() {
    document.getElementById("newchatmenu").addEventListener("focusout", e => {
        if (!e.currentTarget.contains(e.relatedTarget)) {
            document.getElementById("container2").style.filter = "blur(0px)";
            setTimeout(() => {
                document.getElementById("newchatmenu").style.display = "none";
            }, 500);
        }
    });
    document.getElementById("messageinput").addEventListener("keydown", e => {
        if (e.key == "Enter" && e.shiftKey == false) {
            sendMessage();
            e.preventDefault();
            return;
        }
    })
}
async function searchusers() {
    document.getElementById("userlist").innerHTML = "";
    if (document.getElementById("searchusers").value == "") {
        return;
    }
    users = await callapi("usersearch", document.getElementById("searchusers").value);
    for (user in users) {
        let userelement = document.createElement("li")
        let userp = document.createElement("p")
        let userimg = document.createElement("img")
        userimg.src=users[user]['picture']
        userp.textContent=users[user]['username']
        document.getElementById("userlist").appendChild(userelement)
        userelement.appendChild(userimg)
        userelement.appendChild(userp)
    }
}

function chatselectoroptions() {
    
}

async function callapi(arg, val) {
    const response = await fetch(apiurl + "?"+ String(arg) + "="+String(val));
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }
    const json = await response.json();
    return json;
}