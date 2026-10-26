tb470, DUT x230v2-28GS (swi_f, u1) as the AMF master with a USB backup stick and the FULL licence, 2026-10-27 11:01-11:15 NZDT.

| case | title | log | verdict |
| --- | --- | --- | --- |
| T28218 | ATMF provisioning | [28218/28218.log](28218/28218.log) | **PASS**. With `atmf master` on the x230, future_node was provisioned, its directory was created on usb:, the x230's .rel (36747551 B) and tb470-bench.cfg (2184 B) were copied there and set, and `show atmf provision nodes` shows both files "(file exists)". Health clean |
