// wires the existing buttons to the backend

const textarea = document.querySelector("textarea");
const flipL = document.querySelector('input[name="flipL"]');
const flipR = document.querySelector('input[name="flipR"]');
const generateBtn = document.querySelector('button[tag="generate"]');

let player = new Audio();

function play(url) {
    player.pause();
    player = new Audio(url + "&t=" + Date.now()); // dodge the browser cache
    player.play();
}

generateBtn.addEventListener("click", async () => {
    generateBtn.textContent = "Generating...";
    const response = await fetch("/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textarea.value }),
    });
    generateBtn.textContent = response.ok ? "Generate Audios" : "Failed, try again";
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
