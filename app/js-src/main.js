let items = document.getElementsByTagName("li");
for (let i = 0; i < items.length; i++) {
    if (items[i].children[0].href == window.location.href.split('?')[0]) {
        items[i].children[0].className = "nav-link active";
    }
}

let followItems = document.getElementsByClassName("followcount");
for (let i = 0; i < followItems.length; i++) {
    followItems[i].innerText = parseInt(followItems[i].innerText).toLocaleString();
}

let durationItems = document.getElementsByClassName("duration");
for (let i = 0; i < durationItems.length; i++) {
    let full = new Date(parseInt(durationItems[i].innerText)).toISOString().slice(11, 19);
    if (full.slice(0, 2) == "00") {
        full = full.slice(3);
    }
    durationItems[i].innerText = full;
}

let sampleItems = document.getElementsByClassName("sample");
const setItem = (index) => {
    sampleItems = Array.prototype.slice.call(sampleItems);
    let elem = sampleItems[index];
    sampleItems = document.getElementsByClassName("sample");
    for (let i = 0; i < sampleItems.length; i++) {
        sampleItems[i].className = "dropdown-item sample";
    }
    elem.className = "dropdown-item sample active";
}
for (let i = 0; i < sampleItems.length; i++) {
    let currentlySelected = sampleItems[0];
    switch ((new URLSearchParams(location.search)).get("count")) {
        case "5":
            setItem(0);
            break;
        case "10":
            setItem(1);
            break;
        case "25":
            setItem(2);
            break;
        case "50":
            setItem(3);
            break;
    }
}