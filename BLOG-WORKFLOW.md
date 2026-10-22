# HBS Blog — Publishing Workflow

## Every time you publish a Substack post:

### Step 1 — Publish to Substack as normal
Go to timingcodehbs.substack.com and publish your post.

---

### Step 2 — Open Terminal
On your Mac: press **Cmd + Space**, type **Terminal**, hit Enter.

---

### Step 3 — Run the script
Copy and paste this exactly:

```
cd "/Users/robertschantz/Desktop/Claude Code/hbs-website" && python3 substack-to-blog.py
```

Hit Enter. It will print something like:

```
✅  Generated: blog/why-relationships-end-when-they-do.html
    Title:     Why Relationships End When They Do
    Category:  Relationships
    Date:      October 2026

ADD THIS CARD TO blog.html (inside .post-grid):

  <article class="post-card fade-in">
    ...
  </article>
```

---

### Step 4 — Add the card to the blog index
1. Open the file: `/Users/robertschantz/Desktop/Claude Code/hbs-website/blog.html`
2. Find the line that says `<!-- POST GRID -->` (or the last `</article>` inside `.post-grid`)
3. Paste the card snippet the script printed — above the existing cards so newest posts appear first
4. Save the file

---

### Step 5 — Done
The new post is live on the website. Refresh http://localhost:3000/blog.html to confirm.

---

## Commands reference

| What you want | Command |
|---|---|
| Publish latest post | `python3 substack-to-blog.py` |
| See all posts in feed | `python3 substack-to-blog.py --list` |
| Publish all posts at once | `python3 substack-to-blog.py --all` |

---

## If something goes wrong

**"File already exists — skipping"**
The post was already generated. Nothing to do.

**"No posts found"**
Wait a few minutes after publishing — Substack RSS can take 5–10 min to update. Then run again.

**Any other error**
Paste the error message into Claude Code and ask for help.

---

## When you move to GoHighLevel
The GHL team will set up a Zapier automation:
**Substack publishes → GHL creates a blog draft automatically.**
At that point this script and Step 4 go away entirely.
