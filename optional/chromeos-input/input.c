#define _GNU_SOURCE
#ifndef _FORTIFY_SOURCE
#define _FORTIFY_SOURCE 2
#endif
#include <linux/uinput.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <fcntl.h>
#include <unistd.h>
#include <signal.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <time.h>
#include <grp.h>

static int keyboard=-1,mouse=-1,listener=-1,screen_width=1366,screen_height=768;
static char socket_path[108];
static volatile sig_atomic_t running=1;
static void signal_stop(int sig){(void)sig;running=0;if(listener>=0)close(listener);listener=-1;}
static void fatal(const char *s){perror(s);exit(1);}
static void pause_ms(int n){struct timespec t={n/1000,(n%1000)*1000000L};while(nanosleep(&t,&t)<0&&errno==EINTR){}}
static int event(int fd,int type,int code,int value){struct input_event e={0};e.type=type;e.code=code;e.value=value;return write(fd,&e,sizeof e)==sizeof e?0:-1;}
static void sync_device(int fd){event(fd,EV_SYN,SYN_REPORT,0);}
static int device(int pointer){
 int fd=open("/dev/uinput",O_WRONLY|O_CLOEXEC);if(fd<0)fatal("open uinput");
 if(ioctl(fd,UI_SET_EVBIT,EV_KEY)<0)fatal("key event support");
 if(pointer){
  for(int k=BTN_LEFT;k<=BTN_MIDDLE;k++)if(ioctl(fd,UI_SET_KEYBIT,k)<0)fatal("mouse key");
  if(ioctl(fd,UI_SET_EVBIT,EV_ABS)<0)fatal("absolute event support");
  if(ioctl(fd,UI_SET_ABSBIT,ABS_X)<0||ioctl(fd,UI_SET_ABSBIT,ABS_Y)<0)fatal("absolute axes");
  struct uinput_abs_setup axis={0};axis.code=ABS_X;axis.absinfo.maximum=screen_width-1;
  if(ioctl(fd,UI_ABS_SETUP,&axis)<0)fatal("X bounds");
  axis.code=ABS_Y;axis.absinfo.maximum=screen_height-1;
  if(ioctl(fd,UI_ABS_SETUP,&axis)<0)fatal("Y bounds");
  if(ioctl(fd,UI_SET_EVBIT,EV_REL)<0||ioctl(fd,UI_SET_RELBIT,REL_WHEEL)<0)fatal("wheel support");
 }else{for(int k=1;k<256;k++)if(ioctl(fd,UI_SET_KEYBIT,k)<0)fatal("keyboard key");}
 struct uinput_setup setup={0};setup.id.bustype=BUS_USB;setup.id.vendor=0x1209;setup.id.product=pointer?0xB002:0xB001;setup.id.version=1;
 snprintf(setup.name,sizeof setup.name,"Workbench %s",pointer?"Mouse":"Keyboard");
 if(ioctl(fd,UI_DEV_SETUP,&setup)<0||ioctl(fd,UI_DEV_CREATE)<0)fatal("create input device");
 return fd;
}
struct key {const char *name;int code;};
static const struct key keys[]={
 {"ctrl",KEY_LEFTCTRL},{"alt",KEY_LEFTALT},{"shift",KEY_LEFTSHIFT},{"search",KEY_LEFTMETA},
 {"enter",KEY_ENTER},{"esc",KEY_ESC},{"tab",KEY_TAB},{"space",KEY_SPACE},{"backspace",KEY_BACKSPACE},
 {"up",KEY_UP},{"down",KEY_DOWN},{"left",KEY_LEFT},{"right",KEY_RIGHT},{"home",KEY_HOME},{"end",KEY_END},
 {"pageup",KEY_PAGEUP},{"pagedown",KEY_PAGEDOWN},{"delete",KEY_DELETE},{"overview",KEY_SCALE},{"printscreen",KEY_SYSRQ},
 {"f1",KEY_F1},{"f2",KEY_F2},{"f3",KEY_F3},{"f4",KEY_F4},{"f5",KEY_F5},{"f6",KEY_F6},{"f7",KEY_F7},{"f8",KEY_F8},{"f9",KEY_F9},{"f10",KEY_F10},{"f11",KEY_F11},{"f12",KEY_F12},
 {"a",KEY_A},{"b",KEY_B},{"c",KEY_C},{"d",KEY_D},{"e",KEY_E},{"f",KEY_F},{"g",KEY_G},{"h",KEY_H},{"i",KEY_I},{"j",KEY_J},{"k",KEY_K},{"l",KEY_L},{"m",KEY_M},{"n",KEY_N},{"o",KEY_O},{"p",KEY_P},{"q",KEY_Q},{"r",KEY_R},{"s",KEY_S},{"t",KEY_T},{"u",KEY_U},{"v",KEY_V},{"w",KEY_W},{"x",KEY_X},{"y",KEY_Y},{"z",KEY_Z},
 {"0",KEY_0},{"1",KEY_1},{"2",KEY_2},{"3",KEY_3},{"4",KEY_4},{"5",KEY_5},{"6",KEY_6},{"7",KEY_7},{"8",KEY_8},{"9",KEY_9}
};
static int keycode(const char *name){for(size_t i=0;i<sizeof keys/sizeof *keys;i++)if(!strcmp(keys[i].name,name))return keys[i].code;return -1;}
static int hotkey(char *names){
 size_t length=strlen(names);
 if(!length||names[0]=='+'||names[length-1]=='+'||strstr(names,"++"))return -1;
 int codes[8],count=0;char *save=NULL,*s=strtok_r(names,"+",&save);
 while(s){if(count>=8||(codes[count]=keycode(s))<0)return -1;count++;s=strtok_r(NULL,"+",&save);}
 if(!count)return -1;
 for(int i=0;i<count;i++){event(keyboard,EV_KEY,codes[i],1);sync_device(keyboard);pause_ms(15);}
 for(int i=count-1;i>=0;i--){event(keyboard,EV_KEY,codes[i],0);sync_device(keyboard);pause_ms(10);}return 0;
}
static int ascii_code(unsigned char c,int *shift){
 *shift=0;
 if(c>='a'&&c<='z'){char n[2]={(char)c,0};return keycode(n);}
 if(c>='A'&&c<='Z'){char n[2]={(char)tolower(c),0};*shift=1;return keycode(n);}
 if(c>='0'&&c<='9'){char n[2]={(char)c,0};return keycode(n);}
 const char plain[]=" -=[]\\;',./`", shifted[]=" _+{}|:\"<>?~";
 const int codes[]={KEY_SPACE,KEY_MINUS,KEY_EQUAL,KEY_LEFTBRACE,KEY_RIGHTBRACE,KEY_BACKSLASH,KEY_SEMICOLON,KEY_APOSTROPHE,KEY_COMMA,KEY_DOT,KEY_SLASH,KEY_GRAVE};
 for(size_t i=0;i<sizeof codes/sizeof *codes;i++){if(c==plain[i])return codes[i];if(c==shifted[i]){*shift=1;return codes[i];}}
 const char symbols[]="!@#$%^&*()";const int digits[]={KEY_1,KEY_2,KEY_3,KEY_4,KEY_5,KEY_6,KEY_7,KEY_8,KEY_9,KEY_0};
 for(size_t i=0;i<10;i++)if(c==symbols[i]){*shift=1;return digits[i];}
 return -1;
}
static int type_text(char *text){
 if(strlen(text)>1000)return -1;
 for(size_t i=0;text[i];i++){int shift;if(ascii_code((unsigned char)text[i],&shift)<0)return -1;}
 for(size_t i=0;text[i];i++){
  int shift,code=ascii_code((unsigned char)text[i],&shift);
  if(shift){event(keyboard,EV_KEY,KEY_LEFTSHIFT,1);sync_device(keyboard);}
  event(keyboard,EV_KEY,code,1);sync_device(keyboard);pause_ms(7);event(keyboard,EV_KEY,code,0);sync_device(keyboard);
  if(shift){event(keyboard,EV_KEY,KEY_LEFTSHIFT,0);sync_device(keyboard);}pause_ms(7);
 }return 0;
}
static int execute(char *command){
 if(!strcmp(command,"ping"))return 0;
 if(!strcmp(command,"stop")){running=0;return 0;}
 if(!strncmp(command,"key ",4))return hotkey(command+4);
 if(!strncmp(command,"text ",5))return type_text(command+5);
 if(!strncmp(command,"drag ",5)){
  int x1,y1,x2,y2,ms;char tail;
  if(sscanf(command+5,"%d %d %d %d %d %c",&x1,&y1,&x2,&y2,&ms,&tail)!=5||x1<0||x1>=screen_width||x2<0||x2>=screen_width||y1<0||y1>=screen_height||y2<0||y2>=screen_height||ms<100||ms>2000)return -1;
  event(mouse,EV_ABS,ABS_X,x1);event(mouse,EV_ABS,ABS_Y,y1);sync_device(mouse);
  event(mouse,EV_KEY,BTN_LEFT,1);sync_device(mouse);
  for(int step=1;step<=20;step++){event(mouse,EV_ABS,ABS_X,x1+(x2-x1)*step/20);event(mouse,EV_ABS,ABS_Y,y1+(y2-y1)*step/20);sync_device(mouse);pause_ms(ms/20);}
  event(mouse,EV_KEY,BTN_LEFT,0);sync_device(mouse);return 0;
 }
 if(!strncmp(command,"move ",5)){int x,y;char tail;if(sscanf(command+5,"%d %d %c",&x,&y,&tail)!=2||x<0||x>=screen_width||y<0||y>=screen_height)return -1;event(mouse,EV_KEY,BTN_LEFT,0);event(mouse,EV_ABS,ABS_X,x);event(mouse,EV_ABS,ABS_Y,y);sync_device(mouse);return 0;}
 if(!strncmp(command,"scroll ",7)){int y;char tail;if(sscanf(command+7,"%d %c",&y,&tail)!=1||y < -20||y>20)return -1;event(mouse,EV_REL,REL_WHEEL,y);sync_device(mouse);return 0;}
 if(!strncmp(command,"click ",6)){int code=!strcmp(command+6,"left")?BTN_LEFT:!strcmp(command+6,"right")?BTN_RIGHT:!strcmp(command+6,"middle")?BTN_MIDDLE:-1;if(code<0)return -1;event(mouse,EV_KEY,code,1);sync_device(mouse);pause_ms(30);event(mouse,EV_KEY,code,0);sync_device(mouse);return 0;}
 return -1;
}
static int send_all(int fd,const char *buffer,size_t length){
 while(length){ssize_t sent=write(fd,buffer,length);if(sent<0&&errno==EINTR)continue;if(sent<=0)return -1;buffer+=sent;length-=(size_t)sent;}return 0;
}
static int client(const char *path,const char *command){
 if(strlen(path)>=sizeof socket_path||strlen(command)>7000||strchr(command,'\n')||strchr(command,'\r'))return 2;
 int fd=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);if(fd<0)fatal("client socket");
 struct sockaddr_un addr={.sun_family=AF_UNIX};strcpy(addr.sun_path,path);
 if(connect(fd,(struct sockaddr*)&addr,sizeof addr)<0)fatal("connect local control socket");
 dprintf(fd,"%s\n",command);shutdown(fd,SHUT_WR);char out[256];ssize_t n=read(fd,out,sizeof out-1);close(fd);if(n<=0)return 1;out[n]=0;fputs(out,stdout);return strncmp(out,"OK",2)?1:0;
}
int main(int argc,char **argv){
 if(argc==4&&!strcmp(argv[1],"--send"))return client(argv[2],argv[3]);
 if(argc==2&&!strcmp(argv[1],"--version")){puts("Workbench desktop input 0.2.0");return 0;}
 if(argc!=7||strcmp(argv[1],"--daemon")||geteuid()!=0){fputs("Usage: --version | --send SOCKET COMMAND | root: --daemon SOCKET UID GID WIDTH HEIGHT\n",stderr);return 2;}
 if(strlen(argv[2])>=sizeof socket_path)return 2;
 uid_t uid=(uid_t)strtoul(argv[3],NULL,10);gid_t gid=(gid_t)strtoul(argv[4],NULL,10);if(uid==0||gid==0)return 2;
 screen_width=atoi(argv[5]);screen_height=atoi(argv[6]);if(screen_width<320||screen_width>8192||screen_height<320||screen_height>8192)return 2;
 strcpy(socket_path,argv[2]);signal(SIGTERM,signal_stop);signal(SIGINT,signal_stop);signal(SIGPIPE,SIG_IGN);
 keyboard=device(0);mouse=device(1);
 listener=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);if(listener<0)fatal("server socket");
 struct sockaddr_un addr={.sun_family=AF_UNIX};strcpy(addr.sun_path,socket_path);
 unlink(socket_path);umask(0077);if(bind(listener,(struct sockaddr*)&addr,sizeof addr)<0||chown(socket_path,uid,gid)<0||chmod(socket_path,0600)<0||listen(listener,5)<0)fatal("private socket");
 if(setgroups(0,NULL)<0||setgid(gid)<0||setuid(uid)<0)fatal("drop privileges");
 pause_ms(750);
 while(running){
  int fd=accept4(listener,NULL,NULL,SOCK_CLOEXEC);if(fd<0){if(errno==EINTR||!running)continue;fatal("accept");}
  struct timeval timeout={5,0};setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof timeout);
  struct ucred peer;socklen_t size=sizeof peer;
  if(getsockopt(fd,SOL_SOCKET,SO_PEERCRED,&peer,&size)<0||(peer.uid!=uid&&peer.uid!=0)){close(fd);continue;}
  char buf[8192];size_t used=0;int complete=0;
  while(used<sizeof buf-1){ssize_t n=read(fd,buf+used,sizeof buf-1-used);if(n<=0)break;used+=(size_t)n;if(memchr(buf,'\n',used)){complete=1;break;}}
  buf[used]=0;char *newline=strchr(buf,'\n');if(newline)*newline=0;
  if(complete&&!strcmp(buf,"info")){dprintf(fd,"OK width=%d height=%d version=0.2.0\n",screen_width,screen_height);close(fd);continue;}
  int result=complete&&used==strlen(buf)+1?execute(buf):-1;const char *response=result?"ERROR invalid or unsupported command\n":"OK\n";if(send_all(fd,response,strlen(response))<0){close(fd);continue;}close(fd);
 }
 if(listener>=0)close(listener);
 unlink(socket_path);
 ioctl(keyboard,UI_DEV_DESTROY);ioctl(mouse,UI_DEV_DESTROY);close(keyboard);close(mouse);return 0;
}
