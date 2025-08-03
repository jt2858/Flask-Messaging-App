
// Global SocketIO connection variable
var socket = null;

/**
 * Send a message through SocketIO
 * Handles both text messages and messages with images
 */
function sendMessage() {
    const messageInput = document.getElementById("messageinput").value;
        // Only send if message has content
    if (messageInput.trim().length!=0){
        // Clear input field immediately for better UX
        document.getElementById("messageinput").value = null;
        // Check if there's an image attached
        if (document.getElementById("imageuploaddisplay").src!=undefined) {
            // Send message with image data (base64 encoded)
            socket.emit("message", JSON.stringify({"message": messageInput, "sender": socket.id, "room": new URLSearchParams(window.location.search).get("chatid"), "image": String(document.getElementById("imageuploaddisplay").src)}))
            // Clear image display after sending
            document.getElementById("imageuploaddisplay").removeAttribute("src")
        }
        else {
            // Send text-only message
            socket.emit("message", JSON.stringify({"message": messageInput, "sender": socket.id, "room": new URLSearchParams(window.location.search).get("chatid")}))
        }
    }
}
/**
 * Show the new chat creation menu
 * Applies blur effect to background
 */
function shownewchatmenu() {
    if (document.getElementById("newchatmenu").style.display!="flex") {
        document.getElementById("newchatmenu").style.display="flex";
        document.getElementById("newchatmenu").focus();
        document.getElementById("container2").style.filter = "blur(5px)";
    }
}
/**
 * Main initialization function - runs when page loads
 */
window.onload = function() {
    // Initialize SocketIO connection
    socket=io()
    // Hide new chat menu when clicking outside of it
    document.getElementById("newchatmenu").addEventListener("focusout", e => {
        if (!e.currentTarget.contains(e.relatedTarget)) {
            document.getElementById("container2").style.filter = "blur(0px)";
            setTimeout(() => {
                document.getElementById("newchatmenu").style.display = "none";
            }, 500);
        }
    });
    // Handle Enter key press in message input (without Shift for send)
    document.getElementById("messageinput").addEventListener("keydown", e => {
        if (e.key == "Enter" && e.shiftKey == false) {
            sendMessage();
            e.preventDefault();
            return;
        }
    })
    /**
     * Handle incoming messages from SocketIO
     * Creates and displays message elements in real-time
     */
    socket.on("message", async function(data) {
        // Only display message if it's for the currently active chat
        if (String(new URLSearchParams(window.location.search).get("chatid"))==String(JSON.parse(data)['room'])){
            let message = document.createElement("li")
            // Style message based on sender (sent by current user or received)
            if (JSON.parse(data)['sender']==socket.id) {message.setAttribute("sent", "True")}
            else {message.setAttribute("received", "True")}
            let text = document.createElement("p")
            text.textContent=JSON.parse(data)['message']
            message.appendChild(text)
            document.getElementById("chatcontainer").appendChild(message)
            message.scrollIntoView({behavior: "smooth"});
            console.log(JSON.parse(data)['image'])
            // Handle image attachments
            if (JSON.parse(data)['image']!="" && JSON.parse(data)['image']!=undefined) {
                let img =document.createElement("img")
                img.src=JSON.parse(data)['image']
                let imgli = document.createElement("li")
                if (JSON.parse(data)['sender']==socket.id) {imgli.setAttribute("sent", "True")}
                else {imgli.setAttribute("received", "True")}
                imgli.appendChild(img)
                document.getElementById("chatcontainer").appendChild(imgli)
                imgli.scrollIntoView({behavior: "smooth"});
            }

        }
    })
    /**
     * Handle file upload for images
     * Converts uploaded image to base64 for transmission
     */
    document.getElementById("imageupload").onchange = function(event) {
        let file = event.target.files[0]
        const reader = new FileReader();

        // Set up the onloadend event handler
        reader.onloadend = function() {
            const base64String = reader.result; // This will contain the Base64 data URL
            document.getElementById("imageuploaddisplay").src=base64String;
        };

        // Read the file as a Data URL
        reader.readAsDataURL(file);
    }
    
}

// Map to track selected users for new chat creation
const usersselected = new Map();
function editusersselected(user) {
    if (usersselected.has(user)) {
        usersselected.delete(user);
    }
    else {
        usersselected.set(user, usersselected.size);
    }
}
/**
 * Search for users to add to new chat
 * Makes API call and updates UI with search results
 */
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
/**
 * Create new chat with selected users
 * Makes API call and redirects to messenger
 */
async function createchat() {
    arr = []
    for (key of usersselected.keys()) {
        arr.push(key)
    }
    await callapi("createchat", true, JSON.stringify({"users": arr}))
    window.location.href=messengerurl
}

/**
 * Generic API call function
 * arg - API endpoint argument
 * val - API endpoint value
 * body - Optional request body for POST requests

 */
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
