// wires the existing buttons to the backend

const textarea = document.querySelector("textarea");
const flipL = document.querySelector('input[name="flipL"]');
const flipR = document.querySelector('input[name="flipR"]');
const generateBtn = document.querySelector('button[tag="generate"]');
const pauseBtn = document.querySelector('button[tag="P"]');
// remember whatever the button is called, so restoring it cannot rename it
const generateLabel = generateBtn.textContent;

let player = new Audio();

// a little popup message at the bottom of the page
const toast = document.createElement("div");
toast.className = "toast";
document.body.appendChild(toast);
let toastTimer;

function showToast(message) {
    toast.textContent = message;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 3000);
}

// the pause button shows what pressing it will do next
function showPauseState() {
    pauseBtn.innerHTML = player.paused ? "&#9654;" : "&#9208;";
}

async function play(url) {
    const response = await fetch(url + "&t=" + Date.now()); // dodge the browser cache
    if (!response.ok) {
        showToast((await response.json()).detail);
        return;
    }
    player.pause();
    player = new Audio(URL.createObjectURL(await response.blob()));
    // let the audio itself drive the label, so it never lies
    for (const event of ["play", "pause", "ended"]) {
        player.addEventListener(event, showPauseState);
    }
    player.play();
}

generateBtn.addEventListener("click", async () => {
    generateBtn.textContent = "Generating...";
    try {
        const response = await fetch("/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: textarea.value }),
        });
        if (response.ok) {
            showToast("Audios ready! Use L / R / B to play");
        } else {
            showToast((await response.json()).detail);
        }
    } catch {
        showToast("Could not reach the server");
    }
    generateBtn.textContent = generateLabel;
});

document.querySelector('button[tag="L"]').addEventListener("click", () => {
    play("/audio/left?flip=" + flipL.checked);
});

document.querySelector('button[tag="R"]').addEventListener("click", () => {
    play("/audio/right?flip=" + flipR.checked);
});

document.querySelector('button[tag="B"]').addEventListener("click", () => {
    play("/audio/both?flipL=" + flipL.checked + "&flipR=" + flipR.checked);
});

pauseBtn.addEventListener("click", () => {
    if (!player.src) {
        showToast("Nothing is playing yet");
        return;
    }
    if (player.paused) {
        player.play();
    } else {
        player.pause();
    }
});
