let items = document.getElementsByTagName("li");
for (let i = 0; i < items.length; i++) {
    if (items[i].children[0].href == window.location.href) {
        items[i].children[0].className = "nav-link active";
    }
}

let followItems = document.getElementsByClassName("followcount");
for (let i = 0; i < followItems.length; i++) {
    followItems[i].innerText = parseInt(followItems[i].innerText).toLocaleString();
}

let durationItems = document.getElementsByClassName("duration");
for (let i = 0; i < durationItems.length; i++) {
    let full = new Date(parseInt(durationItems[i].innerText)).toISOString().slice(11,19);
    if (full.slice(0,2) == "00") {
        full = full.slice(3);
    }
    durationItems[i].innerText = full;
}