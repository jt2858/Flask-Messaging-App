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

const usersselected = new Map();

function editusersselected(user) {
    if (usersselected.has(user)) {
        usersselected.delete(user);
    }
    else {
        usersselected.set(user, usersselected.size);
    }
}

async function searchusers() {
    if (document.getElementById("searchusers").value == "") {
        document.getElementById("userlist").remove();
        let newul = document.createElement("ul");
        document.getElementById("newchatmenu").appendChild(newul);
        newul.id="userlist";
        return;
    }
    users = await callapi("usersearch", document.getElementById("searchusers").value);
    document.getElementById("userlist").remove();
    let newul = document.createElement("ul");
    for (user in users) {
        let userelement = document.createElement("li");
        let userp = document.createElement("p");
        let userimg = document.createElement("img");
        let usercheckbox = document.createElement("input")
        let usercheckmark = document.createElement("span");
        let userdata = users[user]
        usercheckbox.type="checkbox";
        userimg.src=userdata['picture'];
        userp.textContent=userdata['username'];
        newul.appendChild(userelement);
        userelement.appendChild(userimg);
        userelement.appendChild(userp);
        userelement.appendChild(usercheckbox)
        userelement.appendChild(usercheckmark);
        usercheckbox.onclick=function(){editusersselected(userdata['username'])};
        if (usersselected.has(userdata['username'])) {
            usercheckbox.checked=true;
        }
        userelement.onclick=function(){usercheckbox.click()};
    }
    document.getElementById("newchatmenu").appendChild(newul);
    newul.id="userlist";
}

async function createchat() {
    arr = []
    for (key of usersselected.keys()) {
        arr.push(key)
    }
    await callapi("createchat", true, JSON.stringify({"users": arr}))
    window.location.href=messengerurl
}


async function callapi(arg, val, body=null) {
    let response=""
    if (body) {
        response = await fetch(apiurl + "?"+ String(arg) + "="+String(val), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
        });
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }        
    }
    else {
        response = await fetch(apiurl + "?"+ String(arg) + "="+String(val));
    
    
        if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
        }
        const json = await response.json();
        return json;
    }
}