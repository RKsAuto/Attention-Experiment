// wires the existing buttons to the backend

// the two stimulus boxes, each with its own flip tick
const boxes = {
    a: {
        text: document.querySelector('textarea[name="a"]'),
        flip: document.querySelector('input[name="flipA"]'),
    },
    b: {
        text: document.querySelector('textarea[name="b"]'),
        flip: document.querySelector('input[name="flipB"]'),
    },
};

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

function startPlaying() {
    // play() hands back a promise. Swapping clips quickly rejects it with
    // AbortError, which is harmless, but a browser refusing to play at all
    // would otherwise fail silently in the middle of a session.
    player.play().catch((err) => {
        if (err.name !== "AbortError") {
            showToast("The browser blocked playback, click the page and retry");
        }
    });
}

// which box feeds which ear, e.g. {left: "a", right: "b"}
async function play(ears) {
    const query = new URLSearchParams({ ...ears, t: Date.now() });
    const response = await fetch("/audio?" + query); // t dodges the cache
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
    startPlaying();
}

generateBtn.addEventListener("click", async () => {
    generateBtn.textContent = "Generating...";
    try {
        const response = await fetch("/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                a: boxes.a.text.value,
                b: boxes.b.text.value,
            }),
        });
        if (response.ok) {
            const ready = (await response.json()).ready.join(" and ").toUpperCase();
            showToast(`Box ${ready} ready! Use L / R / B to play`);
        } else {
            showToast((await response.json()).detail);
        }
    } catch {
        showToast("Could not reach the server");
    }
    generateBtn.textContent = generateLabel;
});

// each box's own L and R send just that box to just that ear
for (const button of document.querySelectorAll("button[box]")) {
    button.addEventListener("click", () => {
        const box = button.getAttribute("box");
        const ear = button.getAttribute("tag") === "L" ? "left" : "right";
        play({ [ear]: box, [ear + "_flip"]: boxes[box].flip.checked });
    });
}

// B is the dichotic one: first box in the left ear, second in the right
document.querySelector('button[tag="B"]').addEventListener("click", () => {
    play({
        left: "a", left_flip: boxes.a.flip.checked,
        right: "b", right_flip: boxes.b.flip.checked,
    });
});

pauseBtn.addEventListener("click", () => {
    if (!player.src) {
        showToast("Nothing is playing yet");
        return;
    }
    if (player.paused) {
        startPlaying();
    } else {
        player.pause();
    }
});
