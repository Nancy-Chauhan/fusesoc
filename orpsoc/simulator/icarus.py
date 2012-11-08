import os
import subprocess
from .simulator import Simulator

class SimulatorIcarus(Simulator):

    def __init__(self, system):
        super(SimulatorIcarus, self).__init__(system)
        self.sim_root = os.path.join(self.build_root, 'sim-icarus')

    def configure(self):
        super(SimulatorIcarus, self).configure()
        self._write_config_files()

    def _write_config_files(self):
        icarus_file = 'icarus.scr'

        f = open(os.path.join(self.sim_root,icarus_file),'w')

        for include_dir in self.include_dirs:
            f.write("+incdir+" + include_dir + '\n')
        for rtl_file in self.rtl_files:
            f.write(rtl_file + '\n')
        for tb_file in self.tb_files:
            f.write(tb_file + '\n')

        f.close()

    def build(self):
        super(SimulatorIcarus, self).build()
        
        #Build VPI modules
        for vpi_module in self.vpi_modules:
            try:
                subprocess.check_call(['iverilog-vpi', '--name='+vpi_module['name']] +
                                      ['-I' + s for s in vpi_module['include_dirs']] +
                                      vpi_module['src_files'],
                                      stderr = open(os.path.join(self.sim_root,vpi_module['name']+'.log'),'w'),
                                      cwd = os.path.join(self.sim_root))
            except OSError:
                print("Error: Command iverilog-vpi not found. Make sure it is in $PATH")
                exit(1)
            except subprocess.CalledProcessError:
                print("Error: Failed to compile VPI library " + vpi_module['name'])
                exit(1)
                                      
        #Build simulation model
        if subprocess.call(['iverilog',
                            '-s', 'orpsoc_tb',
                            '-c', 'icarus.scr',
                            '-o', 'orpsoc.elf'],
                           cwd = self.sim_root):
            print("Error: Compiled failed")
            exit(1)
        
    def run(self, args):
        super(SimulatorIcarus, self).run(args)

        #FIXME: Handle failures. Save stdout/stderr. Build vmem file from elf file argument
        if subprocess.call(['vvp', '-n', '-M.',
                            '-l', 'icarus.log'] +
                           ['-m'+s['name'] for s in self.vpi_modules] +
                           ['orpsoc.elf'] +
                           ['+'+s for s in self.plusargs],
                           cwd = self.sim_root,
                           stdin=subprocess.PIPE):
            print("Error: Failed to run simulation")
