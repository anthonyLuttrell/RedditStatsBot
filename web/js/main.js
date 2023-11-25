const JSON_PATH = "https://redditstatsbot.com/json/subreddits.json"

window.onload = async () =>
{
    let list = await (await fetch(JSON_PATH)).json()
        .then((subs) => fillSelect(subs));
};

function fillSelect(subs)
{
    const selectBox = document.getElementById("subreddits-select");
    for (let sub in subs)
    {
        selectBox.add(sub.toString())
    }
}

function displayUsers(users)
{
    const textArea = document.getElementById("output")
    for (let user in users)
    {
        for (let i = 0; i < users[user]["commentId"].length; i++)
        {
            textArea.value += users[user]["commentId"][i] + "   - -   " + users[user]["commentScore"][i] + "\r\n";
        }
    }
}