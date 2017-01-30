Run ./test.sh to the installation.

It will fail if git and dot are not installed.

The output looks like this:

   $ ./test.sh
   test:001:test01:passed Run passed
   test:002:test01:passed Diff passed
   test:003:test02:passed Run passed
   test:004:test02:passed Diff passed
   test:005:test03:passed Run passed
   test:006:test03:passed Diff passed
   test:007:test04:passed Run passed
   test:008:test04:passed Diff passed
   test:009:test05:passed Run passed
   test:010:test05:passed Diff passed
   test:011:test06:passed Run passed
   test:012:test06:passed Diff passed
   test:013:test07:passed Run passed
   test:014:test07:passed Diff passed
   test:015:test08:passed Run passed
   test:016:test08:passed Diff passed

   test:total:passed   16
   test:total:failed    0
   test:total:summary  16

You can run each test individually like this:

   $ rm -rf .git
   $ ./test04.sh

It will attempt to display a PNG image using Preview on Mac or display
on Linux. If you do not want to display the image run the test as
follow:

   $ DISPLAY=false ./test04.sh
