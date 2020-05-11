## Instagram bot

**Note: instagram constantly change their front end so this code won't work unless it is maintained**

You'll need to create the file secrets.py.
This is how my secrets.py looks like:

    dummy_uname, dummy_pass = '***********', '**********'
    real_uname, real_pass   = '***********', '**********'
    alt_uname, alt_pass     = '***********', '**********'
    
    def get_user(req):
    if req == 'real':
        return real_uname, real_pass 
    elif req == 'alt':
        return alt_uname, alt_pass
    else:
        return dummy_uname, dummy_pass





__**Run examples:**__

python3 insta-crawler.py --like-hashtag-photos photooftheday --number 5

python3 insta-crawler.py --like-user-photos 9gag --number 5

python3 insta-crawler.py --follow-hashtag-profiles memes --number 5



Inspired by aj-4/ig-followers
