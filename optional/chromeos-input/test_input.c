#define main input_program_main
#include "input.c"
#undef main
#include <assert.h>
int main(void){
 for(int c=32;c<=126;c++){int shift=-1;assert(ascii_code((unsigned char)c,&shift)>0);assert(shift==0||shift==1);}
 int shift;assert(ascii_code('A',&shift)==KEY_A&&shift==1);assert(ascii_code('a',&shift)==KEY_A&&shift==0);
 assert(ascii_code(':',&shift)==KEY_SEMICOLON&&shift==1);assert(ascii_code('/',&shift)==KEY_SLASH&&shift==0);
 assert(ascii_code('\n',&shift)==-1);assert(ascii_code(200,&shift)==-1);
 assert(keycode("ctrl")==KEY_LEFTCTRL);assert(keycode("overview")==KEY_SCALE);assert(keycode("bogus")==-1);
 char invalid[]="ctrl+bogus";assert(hotkey(invalid)==-1);
 char empty[]="ctrl++a";assert(hotkey(empty)==-1);
 int fds[2];assert(pipe(fds)==0);mouse=fds[1];keyboard=fds[1];
 fcntl(fds[0],F_SETFL,O_NONBLOCK);
 char bad_drag[]="drag 0 0 9999 10 100";assert(execute(bad_drag)==-1);
 struct input_event events[256];assert(read(fds[0],events,sizeof events)==-1&&errno==EAGAIN);
 char drag[]="drag 20 30 120 130 100";assert(execute(drag)==0);
 ssize_t n=read(fds[0],events,sizeof events);assert(n>0&&n%(ssize_t)sizeof(*events)==0);
 int pressed=0,released=0,last_x=-1,last_y=-1;
 for(size_t i=0;i<(size_t)n/sizeof(*events);i++){
  if(events[i].type==EV_KEY&&events[i].code==BTN_LEFT){if(events[i].value)pressed++;else released++;}
  if(events[i].type==EV_ABS&&events[i].code==ABS_X)last_x=events[i].value;
  if(events[i].type==EV_ABS&&events[i].code==ABS_Y)last_y=events[i].value;
 }
 assert(pressed==1&&released==1&&last_x==120&&last_y==130);
 char oversized[1002];memset(oversized,'a',1001);oversized[1001]=0;assert(type_text(oversized)==-1);
 close(fds[0]);close(fds[1]);
 puts("ASCII mapping, invalid shortcuts, bounded drag, button release and text-limit checks passed.");return 0;
}
