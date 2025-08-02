var socket = null;


function sendMessage() {
    const messageInput = document.getElementById("messageinput").value;
    if (messageInput.trim().length!=0){
        document.getElementById("messageinput").value = null;
        socket.emit("message", JSON.stringify({"message": messageInput, "sender": socket.id, "room": new URLSearchParams(window.location.search).get("chatid")}))
    }
}
function shownewchatmenu() {
    if (document.getElementById("newchatmenu").style.display!="flex") {
        document.getElementById("newchatmenu").style.display="flex";
        document.getElementById("newchatmenu").focus();
        document.getElementById("container2").style.filter = "blur(5px)";
    }
}
window.onload = function() {
    socket=io()
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
    socket.on("message", async function(data) {
        if (String(new URLSearchParams(window.location.search).get("chatid"))==String(JSON.parse(data)['room'])){
            let message = document.createElement("li")
            if (JSON.parse(data)['sender']==socket.id) {message.setAttribute("sent", "True")}
            else {message.setAttribute("received", "True")}
            let text = document.createElement("p")
            text.textContent=JSON.parse(data)['message']
            message.appendChild(text)
            //if (JSON.parse(data)['file']!="") {
            //    let img =document.createElement("img")
            //    img.src=JSON.parse(data)['file']
            //    message.appendChild(img)
            //}
            document.getElementById("chatcontainer").appendChild(message)
            message.scrollIntoView({behavior: "smooth"});

        }
    })
    document.getElementById("fileupload").onchange = function(event) {
        let file = event.target.files[0]
        const reader = new FileReader();

        // Set up the onloadend event handler
        reader.onloadend = function() {
            const base64String = reader.result; // This will contain the Base64 data URL
            console.log(base64String); // You can now use this Base64 string
            document.getElementById("fileuploadtext").textContent=file['name'];
            document.getElementById("fileuploaddisplay").src=""
        };

        // Read the file as a Data URL
        reader.readAsDataURL(file);
    }
    document.getElementById("imageupload").onchange = function(event) {
        let file = event.target.files[0]
        const reader = new FileReader();

        // Set up the onloadend event handler
        reader.onloadend = function() {
            const base64String = reader.result; // This will contain the Base64 data URL
            console.log(base64String); // You can now use this Base64 string
            document.getElementById("fileuploadtext").textContent="";
            document.getElementById("fileuploaddisplay").src=base64String;
        };

        // Read the file as a Data URL
        reader.readAsDataURL(file);
    }
    
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
