## Socket
Oh yeh! Is python !!!

It is copy from https://github.com/lxzan/socket

- Worse performance！
- Higher memory used
- Lower security

it maybe the advantages !!!

not so bad !!! 

and to be well !!! 

#### Describe 

i'm sure that you can design it by yourself!!!

- a read event handler
- a write event handler 
- a transfer message parser 
- a request body
- more and more you need to do...

full of freedom, democracy, civilization, harmony, integrity, friendship, patriotism, dedication ...


#### Performance 

until now, an 4000 concurrent with 4 worker request is easy to deal on 2 second

still had test to do

#### Usage  

##### server 
```python
from server import Server
writer = "" #type: BaseWriter object or subclass object
reader = "" #type: BaseReader object or subclass object
app = Server(writer=writer,reader=reader)
app.run()  # max_listen still is a unused character

```


#### client 

no client prepared 




### donate 

look at yourself ...



