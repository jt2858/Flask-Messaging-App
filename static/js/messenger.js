function sendMessage() {
    const messageInput = document.getElementById("messageInput").value;
    console.log("Sending message:", messageInput.value);
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
    })
}
function searchusers() {
    users = callapi("usersearch", document.getElementById("searchusers").value);
    for (user in users) {
        let userelement = document.createElement("li")
        let userp = document.createElement("p")
        let userimg = docmuent.createElement("img")
        userimg.src=users[0]
        userp.textContent=users[1]
        document.getElementById("userlist").appendChild(userelement)
        userelement.appendChild(userimg)
        userelement.appendChild(userp)
    }
}

async function callapi(arg, val) {
    const response = await fetch(apiurl + "?"+ String(arg) + "="+String(val));
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }
    const json = await response.json();
    return json;
}