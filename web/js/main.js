window.onload = async () =>
{
    let users = await (await fetch("https://redditstatsbot.com/test_file.json")).json()
        .then((users) => displayUsers(users.users));
};

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