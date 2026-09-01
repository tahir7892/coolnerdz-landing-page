const fs = require("fs");
let content = fs.readFileSync("index.html", "utf8");

// 1. DOCTYPE
content = content.replace("<!doctype html>", "<!DOCTYPE html>");

// 2. Void elements
content = content.replace("<meta charset=\"UTF-8\" />", "<meta charset=\"UTF-8\">");
content = content.replace("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />", "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">");
content = content.replace(/<br \/>/g, "<br>");
content = content.replace(/<input type=\"email\" placeholder=\"Email address\" \/>/g, "<input type=\"email\" placeholder=\"Email address\">");

// 3. aria-label misuse
content = content.replace(/aria-label=\"CoolNerdz product interface preview\"/g, "role=\"region\" aria-label=\"CoolNerdz product interface preview\"");
content = content.replace(/aria-label=\"Role tabs\"/g, "role=\"tablist\" aria-label=\"Role tabs\"");

// 4. Raw characters
content = content.replace(/Review & edit/g, "Review &amp; edit");

// 5. Submit button
content = content.replace(/<button class=\"btn\" type=\"button\">Join waitlist<\/button>/g, "<button class=\"btn\" type=\"submit\">Join waitlist</button>");

// 6. Inline styles
const cssClasses = `
    .w-82 { width: 82%; }
    .w-64 { width: 64%; }
    .w-48 { width: 48%; }
    .bg-sky { background: var(--sky); }
    .bg-sage { background: var(--sage); }
    .bg-rose { background: var(--rose); }
    .bg-mint { background: var(--mint); }
    .bg-lavender { background: var(--lavender); }
    .tint-sky { --tint: var(--sky); }
    .tint-sage { --tint: var(--sage); }
    .tint-rose { --tint: var(--rose); }
    .tint-mint { --tint: var(--mint); }
    .tint-lavender { --tint: var(--lavender); }
    .tint-aud-1 { --tint: rgba(220,236,247,.74); }
    .tint-aud-2 { --tint: rgba(217,233,209,.8); }
    .tint-aud-3 { --tint: rgba(255,199,184,.82); }
    .tint-aud-4 { --tint: rgba(232,222,244,.78); }
    .tint-aud-5 { --tint: rgba(190,232,212,.78); }
    .tint-aud-6 { --tint: rgba(255,229,184,.76); }
    .mt-18 { margin-top: 18px; }
    .mt-4-0-0 { margin: 4px 0 0; }
    .support-title { margin: 0 0 10px; font-family: var(--display); font-weight: 300; font-size: 38px; line-height: .95; }
    .support-desc { margin: 0; color: rgba(255,255,255,.72); }
`;
content = content.replace("  </style>", cssClasses + "\n  </style>");

content = content.replace(/style=\"width:82%\"/g, "class=\"w-82\"");
content = content.replace(/style=\"width:64%\"/g, "class=\"w-64\"");
content = content.replace(/style=\"width:48%\"/g, "class=\"w-48\"");

content = content.replace(/class=\"audience featured\" style=\"--tint: rgba\(220,236,247,\.74\)\"/g, "class=\"audience featured tint-aud-1\"");
content = content.replace(/class=\"audience\" style=\"--tint: rgba\(217,233,209,\.8\)\"/g, "class=\"audience tint-aud-2\"");
content = content.replace(/class=\"audience\" style=\"--tint: rgba\(255,199,184,\.82\)\"/g, "class=\"audience tint-aud-3\"");
content = content.replace(/class=\"audience featured\" style=\"--tint: rgba\(232,222,244,\.78\)\"/g, "class=\"audience featured tint-aud-4\"");
content = content.replace(/class=\"audience\" style=\"--tint: rgba\(190,232,212,\.78\)\"/g, "class=\"audience tint-aud-5\"");
content = content.replace(/class=\"audience\" style=\"--tint: rgba\(255,229,184,\.76\)\"/g, "class=\"audience tint-aud-6\"");

content = content.replace(/class=\"role-stage\" style=\"margin-top:18px\"/g, "class=\"role-stage mt-18\"");
content = content.replace(/class=\"role-stage hidden\" style=\"margin-top:18px\"/g, "class=\"role-stage hidden mt-18\"");

content = content.replace(/class=\"tag\" style=\"background:var\(--sky\)\"/g, "class=\"tag bg-sky\"");
content = content.replace(/class=\"tag\" style=\"background:var\(--rose\)\"/g, "class=\"tag bg-rose\"");
content = content.replace(/class=\"tag\" style=\"background:var\(--mint\)\"/g, "class=\"tag bg-mint\"");
content = content.replace(/class=\"tag\" style=\"background:var\(--lavender\)\"/g, "class=\"tag bg-lavender\"");

content = content.replace(/class=\"icon\" style=\"--tint:var\(--sky\)\"/g, "class=\"icon tint-sky\"");
content = content.replace(/class=\"icon\" style=\"--tint:var\(--sage\)\"/g, "class=\"icon tint-sage\"");
content = content.replace(/class=\"icon\" style=\"--tint:var\(--rose\)\"/g, "class=\"icon tint-rose\"");
content = content.replace(/class=\"icon\" style=\"--tint:var\(--mint\)\"/g, "class=\"icon tint-mint\"");
content = content.replace(/class=\"icon\" style=\"--tint:var\(--lavender\)\"/g, "class=\"icon tint-lavender\"");

content = content.replace(/class=\"muted\" style=\"margin:4px 0 0\"/g, "class=\"muted mt-4-0-0\"");

content = content.replace(/style=\"margin:0 0 10px;font-family:var\(--display\);font-weight:300;font-size:38px;line-height:\.95\"/g, "class=\"support-title\"");
content = content.replace(/style=\"margin:0;color:rgba\(255,255,255,\.72\)\"/g, "class=\"support-desc\"");

fs.writeFileSync("index.html", content, "utf8");
